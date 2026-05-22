# PCI: Add pci_ats_required() for CXL.cache capable devices

---

## 更新 - 2026-05-21 16:31 UTC

## 核心话题
本邮件讨论围绕为支持 CXL.cache 的设备引入 `pci_ats_required()` 函数的补丁（v6 1/3）展开。该补丁旨在提供一个辅助函数，用于判断 PCI 设备是否必须启用 ATS（Address Translation Services）才能正常工作，尤其是对于 CXL 内存设备而言。在审查过程中，出现了关于 VF（Virtual Function）ATS 继承逻辑是否符 PCIe 规范的问题。

具体来说，补丁中的 `pci_ats_required()` 函数先调用 `pci_ats_supported()` 检查 ATS 扩展能力是否存在，若设备为 VF (`pdev->is_virtfn` 为真)，则转而使用其对应的 PF (`pci_physfn(pdev)`) 进行后续的 CXL ATS 要求判断。这一逻辑的目的是让 VF 继承 PF 的 ATS 需求，因为 VF 自身可能没有独立的 ATS 能力配置，但由于其与 PF 共享某些系统地址转换资源，因此仍需遵循 PF 侧的 ATS 要求。

代码片段如下（来自引用）：
```c
+bool pci_ats_required(struct pci_dev *pdev)
+{
+	if (!pci_ats_supported(pdev))
+		return false;
+
+	/* A VF inherits its PF's requirement for ATS function */
+	if (pdev->is_virtfn)
+		pdev = pci_physfn(pdev);
+
+	return pci_cxl_ats_required(pdev);
```

Bjorn Helgaas 最初基于 sashiko 的反馈表达了对这一 VF 继承逻辑的担忧：sashiko 指出 “According to the PCIe SR-IOV specification (section 9.3.3.1), VFs do not implement the ATS Extended Capability, which means pdev->ats_cap is always 0 for VFs.” 即根据 PCIe SR-IOV 规范的某一节，VF 并不实现 ATS 扩展能力，所以 `pdev->ats_cap` 对 VF 总是 0。如果该说法成立，那么 `pci_ats_supported(pdev)` 对于 VF 将永远返回 false，从而使其无法进入 VF 继承分支，导致逻辑失效。

Bjorn 随后亲自查验了最新的 PCIe 规范。他指出 sashiko 引用的章节号很可能有误：在 PCIe r7.0 中根本没有 9.3.3.1 节；在 PCIe r6.0 中，9.3.3.1 节描述的是 SR-IOV Extended Capability，并未提及 ATS。而在两个版本中，10.5.1 节都是 ATS Extended Capability 的定义，且明确指出 PF 和 VF 均可实现该能力。因此，sashiko 的反馈是基于错误或不准确的规范引用，补丁中的 VF 继承逻辑并无问题。

最终 Bjorn 认可了该补丁的原设计，并给出了 Acked-by：`Acked-by: Bjorn Helgaas <bhelgaas@google.com>`，宣布了审查的正式通过。

## 参与讨论人员
- **Bjorn Helgaas** (helgaas@kernel.org) – 内核 PCI 子系统维护者。
- **Nicolin Chen** – 补丁提交者，邮件中仅出现姓名，未提及完整公司归属，但常见于 NVIDIA 的贡献。
- **sashiko** – 通过 Bjorn 转述其反馈意见，具体身份未完全披露，但可能为前一版本补丁的审阅者。

## 达成的结论
达成了明确结论：原补丁中的 VF ATS 继承逻辑符合 PCIe 规范（PF 和 VF 均可实现 ATS 扩展能力），因此代码无需修改。Bjorn Helgaas 给出了 `Acked-by`，标志着该补丁在 PCI 子系统审查层面获得认可。

## 下一步改进方向
此补丁无需进一步修改。它应当随整个 v6 系列（1/3）被合入相应的开发主线（例如通过 CXL 或 ARM64 树）。没有其他需要继续讨论或额外测试的条目，除非在后续集成过程中出现新的冲突或更高层级的反馈。

## 新增补丁
本邮件并未发布新版本的补丁，仅是对已提交的 v6 补丁的审查回复和 Ack 声明。因此无新增补丁版本。

---

## 更新 - 2026-05-22 17:19 UTC

## 核心话题
本邮件讨论的是针对支持 CXL.cache 功能的 PCIe 设备引入 `pci_ats_required()` 辅助函数，以确保这类设备在 RID（请求者 ID）被 IOMMU 旁路时仍可启用非 PASID 的 ATS（地址转换服务）。补丁提交者 Nicolin Chen 指出，CXL 规范 r4.0 第 3.2.5.13 节明确要求 CXL.cache 设备必须通过 CXL.io 上的 ATS 请求获取主机物理地址（HPA）才能发出 CXL.cache 请求，因此对于这类设备，ATS 需要“始终开启”（always on），而不能仅由 IOMMU 驱动按需（on demand）启用。补丁引入 `pci_ats_required()` 函数，供 IOMMU 驱动扫描 PCI 设备并调整 ATS 策略，首先添加对 CXL.cache 设备的支持，后续将通过 `quirks.c` 文件为 pre-CXL 设备添加类似逻辑。同时，该函数内部会校验 `pci_ats_supported()`，确保不受信任的设备（例如外部端口）不会因为“始终开启”策略而绕过安全限制，从而维护现有针对 ATS 侧信道攻击的安全策略。该补丁获得了多名开发者的审查与测试，包括来自 Intel、NVIDIA、Huawei 等公司的人员，并通过了 Bjorn Helgaas（PCI 子系统维护者）的 Ack。

## 参与讨论人员
- Nicolin Chen (NVIDIA)，补丁作者
- Yi Liu (Intel)，回复 Reviewed-by
- Vikram Sethi (NVIDIA)，提出建议者
- Jason Gunthorpe (NVIDIA)，提出建议者并给出 Reviewed-by
- Jonathan Cameron (Huawei)，给出 Reviewed-by
- Kevin Tian (Intel)，给出 Reviewed-by
- Nirmoy Das (NVIDIA)，测试并给出 Acked-by
- Dave Jiang (Intel)，给出 Reviewed-by
- Bjorn Helgaas (Google)，给出 Acked-by

## 达成的结论
本封邮件中 Yi Liu 对补丁 v6（1/3）给出了 Reviewed-by，表明该版本已获得其认可。结合补丁提交信息中已包含的众多 Reviewed-by/Acked-by，可以判断该补丁在技术方案上已达成共识，准备就绪等待合入。

## 下一步改进方向
该邮件仅涉及对补丁的审查通过，未提出新的修改意见。由于补丁已获得核心子系统和 IOMMU 相关维护者的 Review/Ack，下一步应是无争议地合入相应维护者树，或等待后续版本汇入主线。

## 新增补丁
本邮件未引入新补丁版本。所讨论的补丁版本为 **[PATCH v6 1/3]**，内容为在 PCI 子系统中添加 `pci_ats_required()` 函数并注册 CXL.cache 设备能力。

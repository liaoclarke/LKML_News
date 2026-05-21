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

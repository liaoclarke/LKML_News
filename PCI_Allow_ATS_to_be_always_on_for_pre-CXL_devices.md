# PCI: Allow ATS to be always on for pre-CXL devices

---

## 更新 - 2026-05-20 15:04 UTC

## 核心话题
本邮件讨论的是一个 PCI 子系统的补丁（v5 版本），旨在为不具备完整 CXL 配置空间但仍表现出 CXL 类似特性的设备（称为“pre-CXL”设备，如 NVIDIA 的某些 GPU/NIC）提供**始终启用 ATS（Address Translation Services）** 的能力。传统上，ATS 功能在 IOMMU 旁路（bypass）模式下是按需开启的，只有在启用非零 PASID 的共享虚拟地址（SVA）场景中才会激活。但部分 pre-CXL 设备的行为类似 CXL.cache 设备，即使其请求者 ID（RID）处于 IOMMU 旁路状态，也要求 ATS 持续工作，否则无法正常完成 DMA 地址转换。

补丁引入了 `pci_dev_specific_ats_required()` 的 quirk 函数，该函数维护一个设备 ID 列表，用于识别这类 pre-CXL 设备。在 `pci_ats_required()` 调用链中，如果设备命中该 quirk 列表，则视为“ATS 始终需要”，从而覆盖原有的按需行为。具体实现上，补丁修改了 `drivers/pci/pci.h`、`drivers/pci/ats.c` 和 `drivers/pci/quirks.c`，并在 `CONFIG_PCI_QUIRKS` 和 `CONFIG_PCI_ATS` 配置下增加条件编译支持。

该补丁是系列补丁（v5 2/3）之一，技术动机源于 NVIDIA 在实际硬件中发现的问题：这些 pre-CXL 设备没有实现 CXL DVSEC，但内部架构依赖 ATS 来维护翻译缓存一致性，如果 ATS 被意外关闭，会导致数据正确性问题。解决方案由 Jason Gunthorpe 建议，并获得了来自 NVIDIA、华为、Intel 等多方工程师的审查与测试。

邮件中 Bjorn Helgaas 仅回复了 `Acked-by`，表明他作为 PCI 子系统维护者认可该补丁的合入资格。虽然邮件片段中出现了 `#if defined(CONFIG_ARM64)` 的条件编译（可能是用于 ACPI RC 资源获取的无关代码），但本补丁本身与 ARM64 架构并无直接依赖，讨论仍被归类于 ARM64 相关列表，可能因原始使用场景涉及 ARM64 平台上的 NVIDIA 设备。

## 参与讨论人员
- **Bjorn Helgaas** (kernel.org) — PCI 子系统维护者，提供了 Acked-by。
- **Nicolin Chen** (Nvidia) — 补丁作者。
- **Nirmoy Das** (Nvidia) — 参与了审查与测试。
- **Jonathan Cameron** (Huawei) — 审查者，提供了 Reviewed-by。
- **Jason Gunthorpe** (Nvidia) — 建议者且提供了 Reviewed-by。
- **Kevin Tian** (Intel) — 审查者，提供了 Reviewed-by。
- **Dave Jiang** (Intel) — 审查者，提供了 Reviewed-by。

## 达成的结论
已完全达成共识。补丁获得了从作者、建议者、测试者到多名维护领域审查者的一致赞成，并最终获得了 PCI 维护者 Bjorn Helgaas 的 Acked-by，标志着该补丁可以进入主线的合入流程。邮件中无任何反对意见或需进一步修改的讨论。

## 下一步改进方向
该补丁自身无需进一步改进，可直接合入。但作为系列补丁（2/3）的一部分，下一步可能需等待同系列的其他补丁（如使用该 quirk 的驱动变更）获得必要的审查与确认。同时需注意 quirk 设备 ID 列表将来可能需要随新硬件型号扩展，届时按常规流程增加 ID 即可，不涉及框架改动。

## 新增补丁
本邮件针对的是 **v5** 版补丁，是该补丁的最新版本。Bjorn Helgaas 直接对该版本给出了 Acked-by，未在此线程中发布更新版本。因此无新增补丁。

---

## 更新 - 2026-05-21 13:34 UTC

## 核心话题
本补丁旨在为一种称为“pre-CXL”的 NVIDIA GPU/NIC 设备引入 ATS（Address Translation Services）常开机制。这类设备虽未实现 CXL 配置空间，但具有大量类似 CXL 的属性。与 CXL.cache 能力类似，这些设备即使在 RID 被 IOMMU 旁路的情况下，仍然需要 ATS 功能保持开启，而非仅在启用非零 PASID 的 SVA 场景下才“按需”开启。换句话说，ATS 需要“始终在线”（always on），以支持设备在 IOMMU 旁路模式下的地址翻译需求，避免因 ATS 关闭导致功能异常。

补丁通过以下方式实现该需求：
1. 在 `drivers/pci/quirks.c` 中新增 `pci_dev_specific_ats_required()` 函数，该函数扫描一个预定义的设备 ID 列表（当前仅包含特定的 NVIDIA 设备），返回该设备是否需要强制开启 ATS。
2. 在 `drivers/pci/pci.h` 中声明该函数，并为 `!CONFIG_PCI_QUIRKS || !CONFIG_PCI_ATS` 情况提供空实现。
3. 在 `drivers/pci/ats.c` 的 `pci_ats_required()` 函数中调用此 quirk 检查，若设备命中列表，则同样要求 ATS 启用。

技术动机：CXL 设备协议要求 ATS 始终保持激活以保证缓存一致性，而 NVIDIA 的某些非 CXL 设备内部架构也依赖类似的机制。如果这些设备在 IOMMU 旁路时关闭 ATS，可能导致 DMA 地址转换错误、性能下降或功能失效。Jason Gunthorpe 最初建议以 quirk 方式处理这些非标准化设备，避免修改核心 ATS 逻辑以保持通用性。

补丁已获得多位来自不同公司的维护者和开发者审阅及测试，包括 PCI 子系统维护者 Bjorn Helgaas 的 Ack，说明该方案在 PCI 层面被接受。

## 参与讨论人员
- Nicolin Chen (NVIDIA) —— 补丁作者
- Jason Gunthorpe (NVIDIA) —— 建议者与审阅者
- Nirmoy Das (NVIDIA) —— 审阅者与测试者
- Jonathan Cameron (Huawei) —— 审阅者
- Kevin Tian (Intel) —— 审阅者
- Dave Jiang (Intel) —— 审阅者
- Bjorn Helgaas (Google, PCI 子系统维护者) —— Ack 者

## 达成的结论
本邮件为补丁 v6 的单方面提交，并非讨论型线程。提供的邮件内容仅包含补丁本身及多位审阅/测试者给出的 Reviewed-by、Tested-by 与 Acked-by 标签，无争议或反对意见。因此，可以认为该补丁已获得相关领域维护者与公司的共识，可以纳入主线（或作为该系列的一部分被合并）。但需注意，该补丁是系列的第 2/3 部分，最终是否合并可能还需等待系列中其他补丁的准备情况。

## 下一步改进方向
由于补丁已积累了充分的审阅和 Ack，且作为 PCI 子系统的改动已获得 Bjorn Helgaas 的 Ack，本补丁本身无需再修改。下一步可能涉及：
- 由 PCI 或 IOMMU 子系统的相关维护者将本补丁（及所属系列）排入合并队列。
- 其他架构（如 ARM64）的相关驱动可能需要确认此通用 PCI 改动不会产生副作用，但当前补丁仅在 ATS 相关且配置了 PCI quirk 的范围内生效，风险较低。
- 未来若有更多“pre-CXL”设备需要相同行为，可在 quirk 的设备 ID 列表中追加条目。

## 新增补丁
本邮件即为 `[PATCH v6 2/3]`，即 v6 系列的第 2 个补丁。在本次提供的邮件内，未出现该补丁的更新版本（如 v7）。根据补丁标题，此版本相较之前版本的变化未在邮件正文中列出，但结合上下文，v6 可能已完成所有审阅意见的整合，达到了可合并的状态。

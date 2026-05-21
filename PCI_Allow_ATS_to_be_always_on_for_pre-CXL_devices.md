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

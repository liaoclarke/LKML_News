# PCI: Allow ATS to be always on for CXL.cache capable devices

---

## 更新 - 2026-05-20 10:29 UTC

## 核心话题
本次讨论实际发生在 Linux 内核 PCI 子系统中，并非直接围绕 ARM64 架构，而是关于为支持 CXL.cache 的设备允许始终开启 ATS（Address Translation Services）的补丁（v4）。补丁旨在确保 CXL.cache 设备能够正常工作，因为这类设备要求使用经地址转换的请求（translated requests），而 ATS 正是提供这种转换能力的机制。

邮件片段中，Jason Gunthorpe 提出：“the device requires translated requests to function. This is what CXL.cache implies (IIRC I was told the spec specifically says this)”，明确指出 CXL.cache 设备必须依赖转换后的请求。他因此建议新增一个函数来统一判断设备是否需要转换请求，命名为 `pci_translated_required()`。Nicolin Chen 则建议 IOMMU 驱动可以直接检查 `pci_cxl_is_cache_capable() || pci_dev_specific_is_pre_cxl()`，但 Jason 坚持“I'd rather have a single function.”，即使用单一函数封装判断逻辑，以避免驱动层代码重复和分散。

最终 Nicolin 提议使用 `pci_ats_required()` 作为函数名，理由是 CXL 规范在表述 CXL.cache 需求时明确使用了“ATS”术语，且该命名能与内核中已有的 `pci_ats_*` 系列函数保持一致。这一提议将技术实现与规范术语对齐，并增强代码可读性。整个讨论体现了主线内核子系统中对接口命名和抽象层次的严谨要求，确保补丁在语义和实现上均达到上游合并标准。需要强调的是，虽然邮件线索出现在用户指定的“ARM64 architecture”上下文，但实际内容完全属于 PCI/CXL 子系统，与 ARM64 没有直接关系，可能是分析请求中的不准确分类。

## 参与讨论人员
- Nicolin Chen (NVIDIA)
- Jason Gunthorpe

## 达成的结论
讨论已达成共识：将使用单一函数来封装设备是否需要 ATS 的判断逻辑，函数名最终确定为 `pci_ats_required()`。Jason Gunthorpe 对 Nicolin 的命名提议未提出反对意见，且该命名符合 CXL 规范中对 ATS 的明确引用，并与现有 PCI ATS 函数系列命名风格一致。

## 下一步改进方向
下一步需要将 `pci_ats_required()` 函数实际实现到补丁中，并在 IOMMU 相关驱动中调用该函数，替代原本零散的条件检查（如 `pci_cxl_is_cache_capable()` 等）。此外，可能需要补充相应的文档注释，说明该函数与 CXL.cache 规范的关系，以及为何 ATS 必须开启。由于这只是补丁 v4 中的一部分，整体补丁系列还需经过更多的测试和审查，特别是确保其在各种 CXL 配置和 IOMMU 类型下的正确性。

## 新增补丁
本邮件线索中未发布新版本的完整补丁，仅对现有 v4 补丁中的函数命名细节进行了后续讨论与确认。

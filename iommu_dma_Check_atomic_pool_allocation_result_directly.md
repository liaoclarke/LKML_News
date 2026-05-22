# iommu/dma: Check atomic pool allocation result directly

---

## 更新 - 2026-05-22 09:58 UTC

## 核心话题
该补丁针对 ARM64 架构下 IOMMU 非阻塞、非一致性 DMA 分配路径的一个潜在缺陷进行修复。在 `iommu_dma_alloc` 函数中，当系统启用了 `CONFIG_DMA_DIRECT_REMAP` 且分配标志不允许阻塞、且分配非一致性内存时，代码会调用 `dma_alloc_from_pool` 从原子池分配页面。此函数的设计是返回已分配的 `struct page *`，并通过参数填充 CPU 虚拟地址，但在 IOMMU 映射场景下，CPU 虚拟地址往往不被需要，因此函数可能仅成功分配页面而令 `cpu_addr` 保持为 NULL。原代码却用 `cpu_addr` 是否为空来判断分配成败，导致合法的成功分配被误判为失败，从而提前返回 NULL，中断了正常的 IOMMU 映射过程。

引用的原始提交 `9420139f516d ("dma-pool: fix coherent pool allocations for IOMMU mappings")` 曾试图修正一致性池分配在 IOMMU 下的行为，但可能忽视了对 `iommu_dma_alloc` 中相应判断逻辑的适配，进而引入此 bug。本补丁将分配检查直接基于 `page` 指针：若 `dma_alloc_from_pool` 返回的 `page` 非空，则认为分配成功并继续执行 IOMMU 映射；若 `page` 为空则返回 NULL。对于其他分配路径（如需要睡眠或一致性分配），保持原有的通过 `cpu_addr` 判断的逻辑。补丁通过分离两条路径的判断条件，彻底消除了依赖 `cpu_addr` 这一不可靠信号的隐患，确保非阻塞、非一致性 DMA 分配能够正确进入 IOMMU 映射阶段，增强了代码的健壮性。

## 参与讨论人员
- Aneesh Kumar K.V (Arm) <aneesh.kumar@kernel.org>（作者、提交者）

## 达成的结论
该补丁作为独立修复提交，未引发讨论，作者详细说明了修复理由和代码改动，可以认为作者自身已达成明确结论：必须直接检查 `page` 指针而非 `cpu_addr` 来判断原子池分配是否成功，以避免误判。

## 下一步改进方向
该补丁需要被审查并合入主线内核。由于处于 v5 补丁系列中的第 16 个，可能还需要与系列中的其他补丁一同接受测试和集成；对于该具体修复，应确保在各种原子上下文及 IOMMU 映射场景下不再出现因 `cpu_addr` 为 NULL 而错误返回的情况，并检验 `dma_alloc_from_pool` 的返回语义是否在其他调用点也有一致处理。

## 新增补丁
本邮件即为 PATCH v5 16/20，未在讨论中引出新的补丁版本，维持 v5。

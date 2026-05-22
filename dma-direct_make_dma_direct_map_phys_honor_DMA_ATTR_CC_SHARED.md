# dma-direct: make dma_direct_map_phys() honor DMA_ATTR_CC_SHARED

---

## 更新 - 2026-05-22 09:58 UTC

## 核心话题
本邮件为 `[PATCH v5 10/20]` 系列补丁中的一封，主题是让 `dma_direct_map_phys()` 函数能够根据 `DMA_ATTR_CC_SHARED` 属性来选择合适的 DMA 地址编码方式。其核心动机在于机密计算（Confidential Computing）场景下，如 ARM64 Realm 世界或 x86/s390/powerpc 的加密虚拟机，设备访问内存时需要对地址进行加密或解密处理。此前，这类平台往往通过强制开启 SWIOTLB（`SWIOTLB_FORCE`）来保证 DMA 安全，但这种方式带来了不必要的弹跳缓冲开销。

该补丁提出更精细化的方案：在 `dma_direct_map_phys()` 中，若调用者通过 `DMA_ATTR_CC_SHARED` 属性标记了映射需要共享（即非加密），则使用 `phys_to_dma_unencrypted()` 将物理地址转换为对应的未加密 DMA 地址；否则使用 `phys_to_dma_encrypted()`。特别地，当设备要求使用未加密 DMA，但给定的源物理地址仍是加密状态时，补丁会强制将映射路由到 SWIOTLB，以确保 DMA 地址与后备内存的属性保持一致。

为实现这一改变，补丁同步修改了多个架构在机密计算初始化时不再设置 `SWIOTLB_FORCE` 标志位，具体涉及 `arch/arm64/mm/init.c`、`arch/powerpc/platforms/pseries/svm.c`、`arch/s390/mm/init.c` 和 `arch/x86/kernel/pci-dma.c`。以 arm64 为例，原代码在 `is_realm_world()` 为真时会同时设置 `swiotlb = true` 和 `flags |= SWIOTLB_FORCE`，现在移除了 `SWIOTLB_FORCE`，仅保留 `swiotlb = true`。这样 SWIOTLB 仍然会初始化，但不再强制所有 DMA 映射都经过弹跳缓冲区，而是由 `dma-direct` 根据属性按需使用，提升了性能与灵活性。补丁还提及从 v3 版本以来新增了 `DMA_ATTR_MMIO` 的处理，说明该系列在不断演进。

## 参与讨论人员
- Aneesh Kumar K.V (Arm), 补丁作者，来自 Arm。
- Jiri Pirko (Nvidia)，提供了 `Tested-by` 标签，来自 Nvidia。

## 达成的结论
本邮件是独立的补丁提交，邮件线程中未见后续讨论或审核意见，因此尚未形成任何公开结论。是否采纳该补丁需等待维护者及社区的审核反馈。

## 下一步改进方向
此补丁作为 v5 系列的一部分，下一步需要：
1. 等待相关子系统的维护者（如 DMA 映射、arm64、x86 等领域）对补丁的代码审查。
2. 验证在多种机密计算平台（Realm、SEV、TDX、secure PPC guest 等）上未强制 SWIOTLB 时的正确性与性能影响。
3. 确保新增的 `DMA_ATTR_MMIO` 处理逻辑与现有使用该属性的驱动协调一致。
4. 根据审查意见继续迭代，可能存在代码风格、逻辑细节或架构覆盖面上的改进要求。

## 新增补丁
本邮件即为该系列的第 10 个补丁，版本为 v5。相比 v3 的变更记录显示：
- v5 中新增了对 `DMA_ATTR_MMIO` 的处理（在 patch 中通过 `Changes from v3` 行简要说明）。

# dma-direct: use DMA_ATTR_CC_SHARED in alloc/free paths

---

## 更新 - 2026-05-22 09:57 UTC

## 核心话题
该补丁（[PATCH v5 04/20]）由 Aneesh Kumar K.V 提交，主题是为 `dma-direct` 分配路径引入 `DMA_ATTR_CC_SHARED` 属性的内部使用，以统一处理强制要求非加密（decrypted/DMA-coherent）的设备场景。问题背景涉及 ARM64 平台上机密计算/内存加密（如 ARM CCA 或类似的 CoCo 环境）对 DMA 一致性和加密属性的敏感控制。

技术动机是：当设备驱动通过 `force_dma_unencrypted(dev)` 表明其必须访问以明文/共享方式分配的 DMA 内存时，现有的 `dma_direct_alloc()`、`dma_direct_free()` 和 `dma_direct_alloc_pages()` 路径中分散地判断 `force_dma_unencrypted()`，导致代码冗余且决策点不一致。补丁的核心做法是，在分配入口处检查 `force_dma_unencrypted(dev)`，若为真，则立即将 `DMA_ATTR_CC_SHARED` 置入 `attrs` 变量中，并将 `mark_mem_decrypt` 设为 true。后续所有需要区分加密/共享内存的地方，均通过检测 `attrs & DMA_ATTR_CC_SHARED` 来统一决策，例如：
- 在 `dma_direct_alloc()` 中，若调用者传入了 `DMA_ATTR_CC_SHARED`，则直接返回 NULL，以防止该内部属性被外部误用（补丁注释中明确说明该属性不是调用者可见的 `dma_alloc_*()` 属性）。
- 对于 `DMA_ATTR_NO_KERNEL_MAPPING` 路径的快速切片，原来的条件是 `!force_dma_unencrypted(dev)`，现改为只有在 `attrs` 中未设置 `DMA_ATTR_CC_SHARED`（即 `(attrs & (DMA_ATTR_NO_KERNEL_MAPPING | DMA_ATTR_CC_SHARED)) == DMA_ATTR_NO_KERNEL_MAPPING`）时才走无映射分配路径，否则会回退到后续的普通分配，以正确处理加密/解密。
- 在 `dma_direct_free()` 中，相应的解密/加密恢复动作也改为依赖 `attrs` 中的 `DMA_ATTR_CC_SHARED`，确保分配与释放的对称性。
- `dma_direct_alloc_pages()` 也同步析出同样的逻辑，将 `force_dma_unencrypted()` 的结果折叠进 `attrs` 再传递给底层函数。

关键引用：
> “DMA_ATTR_CC_SHARED is not a caller-visible dma_alloc_*() attribute. The direct allocator uses it internally after it has decided that the backing pages must be shared/decrypted, so the rest of the allocation path can consistently select DMA addresses, choose compatible pools and restore encryption on free.”

这展示了补丁的设计哲学：将“设备是否需要共享/解密”的一次性决策转化为内部属性，贯穿整个分配-映射-释放流程，从而消除对 `force_dma_unencrypted()` 的多次调用，并使代码逻辑更清晰、更一致。该补丁是系列第 4/20，表明这是对 ARM64 机密计算场景下 DMA direct 路径的重构或增强的一部分，可能后续补丁会进一步基于该属性做池选择或地址转换。

## 参与讨论人员
- Aneesh Kumar K.V (Arm) <aneesh.kumar@kernel.org> — 补丁作者  
- Jiri Pirko (Nvidia) <jiri@nvidia.com> — 提供了 Tested-by 标签，表明其参与了测试

（该邮件为补丁提交邮件，未显示其他讨论者。）

## 达成的结论
此为补丁提交，尚未形成讨论共识或结论。补丁作为 v5 系列的一部分发布，未在本邮件线程中看到后续评审意见或反对观点，因此目前无明确结论，仅处于待审核状态。

## 下一步改进方向
- 需要 DMA 子系统以及 ARM64 架构维护者审核该补丁的逻辑正确性，尤其是 `DMA_ATTR_CC_SHARED` 内部使用的限定是否完备，以及是否会对 `dma_direct_alloc_no_mapping` 等快速路径造成意外影响。
- 确认 `DMA_ATTR_CC_SHARED` 与现有 `DMA_ATTR_NO_KERNEL_MAPPING` 的组合判断无误，且不会破坏对 SWIOTLB 强制分配设备的兼容性。
- 查看整个 20 补丁系列的其他部分是否

# dma-mapping: Use DMA_ATTR_CC_SHARED through direct, pool and swiotlb paths

---

## 更新 - 2026-05-22 09:57 UTC

## 核心话题

本邮件讨论的补丁系列（v5）旨在统一处理 DMA 缓冲区在加密与解密状态下的路径，使 DMA_ATTR_CC_SHARED 属性能够贯穿 dma-direct、dma-pool 和 swiotlb 三大分配路径。当前内核中，直接 DMA（dma-direct）路径主要通过 `force_dma_unencrypted()` 来判断是否需要解密共享缓冲区，但这种方式分散且低效。本系列的动机是将所有与 CC（机密计算）共享/解密相关的决策集中到顶层函数中，让余下的 DMA 接口完全依赖 DMA 属性来做正确判断，从而消除隐式假设，使代码更健壮。

具体技术要点包括：

1. **将 swiotlb 支持的分配移出 `__dma_direct_alloc_pages()`**，使逻辑更清晰。
2. **在 dma-direct 的 alloc/free 路径中传播 DMA_ATTR_CC_SHARED**，让直接分配也能感知共享属性。
3. **原子 DMA 池（atomic DMA pools）增加对加密与解密状态的跟踪**，避免混用。
4. **swiotlb 池跟踪加密状态并强制选择正确池**，防止错误将解密数据放入加密池或反之。
5. **通过 DMA 属性在 `dma_pgprot()` 中集中处理加密/解密的 pgprot 生成**，取代过去的分散逻辑。
6. **将 DMA 属性传递到 `dma_capable()` 检查中**，使能力验证能判断所选 DMA 地址编码是否与 DMA_ATTR_CC_SHARED 匹配。
7. **让 `dma_direct_map_phys()` 根据 DMA_ATTR_CC_SHARED 选择 DMA 地址编码**，并在无法使用直接映射时回退到 swiotlb。这使得 arm64 和 x86 的 CCA 客户机不再需要强制开启 SWIOTLB_FORCE 来完成 DMA 映射，进一步优化了机密虚拟化场景下的 DMA 性能。
8. **从选定的 swiotlb 池状态派生出最终返回的 DMA 地址**，保证地址语义一致。

本次 v5 的变化很大程度上基于 Sashiko 的评审意见，新增了若干修补：
- swiotlb：为动态池保留分配的虚拟地址；
- dma：用物理地址释放原子池页面；
- dma/swiotlb：处理 set_memory_decrypted() 失败的情况；
- dma/swiotlb：从进程上下文释放动态池；
- iommu/dma：直接检查原子池分配结果。

此外还纳入了 pKVM 和 s390 的依赖改动，但明确标注这些尚未准备好合并，正等待子系统测试反馈。同时，本版本移除了 AMD GART 相关补丁，因为其需要更广泛的测试。

## 参与讨论人员

- Aneesh Kumar K.V (Arm) <aneesh.kumar@kernel.org>：本补丁系列的主要提交者。
- （未在邮件中直接出现的评审者）Sashiko（确认真实姓名未给出），他的评审是 v5 变化的重要来源。

## 达成的结论

本邮件仅包含补丁系列的 cover letter，线程中没有显示任何回复或讨论。因此目前尚未达成共识，该系列仍处于待审状态，等待社区维护者的评审以及相关子系统的测试反馈。

## 下一步改进方向

1. **补丁审查**：需要 dma-mapping 维护者、arm64 和 s390 架构维护者等进行详细代码审查。
2. **测试反馈**：pKVM 和 s390 相关的依赖改动需要各自子系统的测试确认，AMD GART 补丁也需要在更广范围内测试后才能重新纳入系列。
3. **讨论与整合**：如果审查中提出新的意见，可能需要调整补丁，例如进一步统一 `force_dma_unencrypted()` 的移除方式，或者改进 swiotlb 池状态跟踪的实现细节。
4. **最终合并**：在所有依赖和核心改动获得 Ack 且测试通过后，可将整个系列合并到内核主线中。

## 新增补丁

本邮件线程中提交的是 **v5** 补丁系列，相比 **v4** 的主要变化包括：

- **新增补丁**（基于 Sashiko 的评审）：
  - swiotlb: Preserve allocation virtual address for dynamic pools
  - dma: free atomic pool pages by physical address
  - dma: swiotlb: handle set_memory_decrypted() failures
  - dma: swiotlb: free dynamic pools from process context
  - iommu/dma: Check atomic pool allocation result directly
- **纳入依赖**：pKVM 和 s390 的相关改动（暂不单独合并，仅作为上下文提供，等待子系统测试）。
- **移除补丁**：AMD GART 相关补丁被移除，待更充分测试后可能再次提交。

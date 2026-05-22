# dma-direct: swiotlb: handle swiotlb alloc/free outside __dma_direct_alloc_pages

---

## 更新 - 2026-05-22 09:57 UTC

## 核心话题
该邮件是 Aneesh Kumar K.V 提交的 v5 版本补丁系列的第三份补丁，主题为将 swiotlb 的分配与释放逻辑从 `__dma_direct_alloc_pages()` 中剥离，转移到 `dma_direct_alloc()` 和 `dma_direct_alloc_pages()` 中统一处理。其核心动机是简化后续基于 DMA 属性标志控制内存加解密（memory encryption/decryption）的流程，特别是在 ARM64 等架构上涉及机密计算或内存加密的场景。

当前主线代码中，`__dma_direct_alloc_pages()` 既处理普通页面分配，又负责 swiotlb 分配，同时在该函数内部调用 `dma_set_decrypted()`/`dma_set_encrypted()` 来修改页面属性。但由于 swiotlb 的底层页面在初始化时（通过 `swiotlb_update_mem_attributes()` 或 `rmem_swiotlb_device_init()`）已经被映射为解密状态（decrypted），dma-direct 层不应再对这些页面重复执行加密/解密转换。重复操作不仅多余，还可能导致错误的内存属性状态，尤其在机密计算环境下会破坏安全隔离。

补丁在逻辑上做了三点核心调整：
1. 将 swiotlb 的分配和释放从 `__dma_direct_alloc_pages()` 中剥离，改为在 `dma_direct_alloc()` / `dma_direct_alloc_pages()` 中显式调用 `swiotlb_alloc()` / `swiotlb_free()`。这样 `__dma_direct_alloc_pages()` 专职处理普通 DMA 分配，避免了加密属性修改与 swiotlb 页面的冲突。
2. 在分配和释放路径中增加对 swiotlb 支撑页面的检测，若检测到页面来自 swiotlb，则跳过 `dma_set_decrypted()` 和 `dma_set_encrypted()` 调用，因为这些页面已由 swiotlb 层正确地解密了。
3. 针对 `restricted-dma-pool` 场景，保持了原有语义：`for_alloc = true` 表示使用 swiotlb 分配，而 `rmem_swiotlb_device_init()` 已预先将整个池解密，并且该池通常与 `shared-dma-pool` 协作，通过 remap/ioremap 访问共享内存，返回的地址本身就适用于解密内存访问，因此现有路径无需改动。

此外，补丁还新增了 `swiotlb_free_from_pool()` 辅助函数，并对 `dma_direct_alloc_pages()` 中 swiotlb 分配不能使用高端内存的限制予以保留。

## 参与讨论人员
- Aneesh Kumar K.V (Arm)（补丁作者）
- Jiri Pirko (nvidia)（Tested-by 标签提供者）

## 达成的结论
由于整个邮件线程仅包含这一封补丁提交，没有后续的评审或讨论回复，因此未形成任何讨论或结论。补丁尚处于提交待审状态。

## 下一步改进方向
补丁需要经过 DMA 映射子系统及 swiotlb 相关维护者的评审。可能的改进方向包括：
- 审查 `is_swiotlb_buffer()` 等检测逻辑是否足够健壮，避免误判。
- 确认在受限 DMA 池（restricted-dma-pool）与共享 DMA 池（shared-dma-pool）协同工作时，加密/解密跳过是否完全正确，特别是涉及设备热插拔或者内存热添加的边界情况。
- 结合整个补丁系列的其他部分，验证此次重组能否确实为后续的属性标志简化奠定基础，并避免引入新的竞态条件。

## 新增补丁
在本邮件线程中，仅有 `[PATCH v5 03/20]` 该补丁的新版本被张贴。其相对于之前版本的主要变更已在提交说明中体现：将 swiotlb 分配/释放移至 `dma_direct_alloc()`/`dma_direct_alloc_pages()` 并增加对 swiotlb 页面不重复加密/解密的处理，同时新增 `swiotlb_free_from_pool()` 辅助函数。

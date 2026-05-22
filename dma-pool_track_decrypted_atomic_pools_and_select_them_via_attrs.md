# dma-pool: track decrypted atomic pools and select them via attrs

---

## 更新 - 2026-05-22 09:58 UTC

## 核心话题
该邮件讨论的是针对 ARM64 架构（尤其是机密计算场景，如 Arm CCA）的 DMA 原子池（atomic DMA pool）改进。核心动机在于支持加密内存（private/encrypted memory）与非加密内存（shared/unencrypted memory）的 DMA 分配隔离。在机密计算环境中，设备访问内存时需要通过 DMA 属性区分加密或共享/未加密的内存，因此 DMA 池也需要相应感知，确保分配时从正确的池中挑选内存块。

补丁的具体技术做法为：
- 引入一个封装结构 `dma_gen_pool`，用于记录原子池是否为未加密（decrypted）状态。
- 在初始化原子池时根据当前系统的安全需求标记该状态。
- 修改 `dma_alloc_from_pool()` 以接收新的 `attrs` 参数，并在遍历可用原子池时，跳过那些加密/未加密状态与 `DMA_ATTR_CC_SHARED` 属性不匹配的池。
- 同步更新 `dma_free_from_pool()` 路径以保证释放时也能正确处理。
- 在 swiotlb 的原子分配路径上传递 `DMA_ATTR_CC_SHARED`，使得从软件 I/O TLB 分配的解密内存会从正确的原子池中获取。

这一改动出现在 `drivers/iommu/dma-iommu.c`、`include/linux/dma-map-ops.h`、`kernel/dma/direct.c`、`kernel/dma/pool.c` 和 `kernel/dma/swiotlb.c` 等多个核心 DMA 文件中，说明其影响范围较广。补丁是系列 `[PATCH v5 05/20]` 的一部分，表明这是一个较大特性开发（如 ARM64 机密计算 DMA 支持）的组件。从测试与审阅标签看，更改已通过 Jiri Pirko (NVIDIA) 的测试和 Mostafa Saleh (Google) 的审阅。

## 参与讨论人员
- **Aneesh Kumar K.V** (Arm) — 补丁提交者，Arm 公司工程师。
- **Jiri Pirko** (nvidia) — 提供了 `Tested-by` 标签。
- **Mostafa Saleh** (smostafa@google.com) — 提供了 `Reviewed-by` 标签。
（邮件线索中可能还包括其他接收者，但提供的片段仅显示上述直接参与审阅和测试的人员。）

## 达成的结论
由于邮件线索中仅提供了补丁提交邮件，未发现任何反对意见或进一步讨论，因此当前状态是补丁已发布，并获得了测试和审阅的认可。尚未见到维护者明确同意合并的回复，因此严格来说没有形成“结论”。但从社区惯例看，一个补丁获得 `Tested-by` 和 `Reviewed-by` 后，通常可以进入维护者树等待合并，可以视为审阅阶段的初步共识——补丁在技术上是可接受的。

## 下一步改进方向
- 等待 DMA 子系统维护者（如 Christoph Hellwig、Jason Gunthorpe 等）的最终审阅和 Ack。
- 若该补丁依赖于系列中的其他补丁（v5 系列 05/20），则需要确保整个系列一致且通过所有测试。
- 可能需要进一步覆盖更多硬件平台的测试，确认加密/未加密池的动态扩展（expand/resize）路径在高负载下稳定。
- 确认与现有 DMA 属性处理方式的兼容性，避免破坏过往无 `DMA_ATTR_CC_SHARED` 的普通分配路径。
- 没有明显未解决的争论，但如果之后有人提出改进意见，则可能需要更新补丁。

## 新增补丁
- 本邮件即为 **PATCH v5 05/20** 补丁，是“跟踪解密原子池并通过属性选择”功能的第五版提交。
- 补丁版本号：v5
- 改动摘要：
  - `dma_gen_pool` 新增解密状态字段。
  - 原子池创建、扩展、调整大小时同步此状态。
  - `dma_alloc_from_pool()` / `dma_free_from_pool()` 增加 `attrs` 参数以匹配池状态。
  - swiotlb 原子分配路径传入 `DMA_ATTR_CC_SHARED`。

# dma-direct: select DMA address encoding from DMA_ATTR_CC_SHARED

---

## 更新 - 2026-05-22 09:58 UTC

## 核心话题
该邮件是Linux内核ARM64架构相关的一个补丁提交，具体属于`dma-direct`子系统改动系列（`[PATCH v5 12/20]`）。讨论线程本身只有补丁正文，无后续回复，因此核心是补丁所解决的技术问题与实现方式。

补丁的核心动机是**解耦DMA地址编码与强制内存解密（force_dma_unencrypted）之间的隐式依赖**，改为显式根据`DMA_ATTR_CC_SHARED`属性来选择加密或非加密地址编码。在原有代码中，`phys_to_dma_direct()`内部通过`force_dma_unencrypted(dev)`判断是否需要生成未加密地址，这使得**地址编码逻辑与CoCo（Confidential Computing）相关策略深度绑定**，且分配路径返回的DMA地址无法灵活匹配缓冲区的加密状态。作者Aneesh Kumar明确指出了这一设计缺陷，并提出由调用者传递一个明确的`unencrypted`布尔参数，从而将加密属性的决策提升到DMA属性处理层。

关键变更包括：
- 将`phys_to_dma_direct()`签名改为接受`bool unencrypted`参数，并据此选择`phys_to_dma_unencrypted()`或`phys_to_dma_encrypted()`，而不再依赖`force_dma_unencrypted()`。
- 在分配路径中，根据是否设置`DMA_ATTR_CC_SHARED`来传递该`unencrypted`标志，使得**返回的DMA地址与请求的缓冲区加密状态一致**。
- 仅在`DMA_ATTR_CC_SHARED`有效时才调用`dma_set_decrypted()`，避免无谓的内存区域状态切换。

补丁在`dma_direct_get_required_mask()`、`dma_coherent_ok()`等函数中更新了调用方式，例如将`phys_to_dma_direct(dev, phys)`改为`phys_to_dma_direct(dev, phys, require_decrypted)`，其中`require_decrypted`来自`force_dma_unencrypted(dev)`，**保持了现有行为但使路径显式化**。

整体上，该补丁是系列中第12个，目标是为后续更精细的DMA地址编码策略（如CoCo虚拟机下的共享/私有内存区分）打下基础。测试由Jiri Pirko完成，来自NVIDIA。由于是单纯的代码提交，无反驳或不同意见，但也可视为等待社区评审的状态。

## 参与讨论人员
- **Aneesh Kumar K.V** (Arm公司) —— 补丁作者、提交者。
- **Jiri Pirko** (NVIDIA) —— 提供测试标签（Tested-by）。

## 达成的结论
本邮件为补丁提交，无后续讨论，因此**未形成明确的评审结论或共识**。补丁作为系列的一部分，尚未收到其他开发者的审核意见或Ack。

## 下一步改进方向
1. **代码审查**：需要至少一位DMA子系统或ARM64架构维护者对补丁进行审查，确认逻辑正确且与系列其它补丁兼容。
2. **扩展测试**：除NVIDIA环境外，可能需要在更多CoCo平台（如AMD SEV、Intel TDX）上验证加密/非加密DMA地址的行为符合预期。
3. **文档/注释更新**：如有必要，为`phys_to_dma_direct()`新增的参数添加清晰的注释，说明其与`DMA_ATTR_CC_SHARED`的关联。
4. **整合到系列中**：该补丁属于v5补丁集的一部分，需确保整个系列通过审查并合并到主线。

## 新增补丁
- **PATCH v5 12/20**：`dma-direct: select DMA address encoding from DMA_ATTR_CC_SHARED`
  - 将`phys_to_dma_direct()`改为接受显式`unencrypted`参数。
  - 在分配/检查函数中根据`DMA_ATTR_CC_SHARED`传递加密状态。
  - 仅在属性存在时调用`dma_set_decrypted()`。
  - 针对`kernel/dma/direct.c`的修改：插入25行，删除17行。

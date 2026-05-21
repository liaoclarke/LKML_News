# dma: swiotlb: track pool encryption state and honor DMA_ATTR_CC_SHARED

---

## 更新 - 2026-05-21 22:50 UTC

## 核心话题

该邮件片段来自 Linux 内核 ARM64 架构下关于 SWIOTLB（软件 I/O TLB）加密池支持的讨论，主线补丁为 `[PATCH v4 04/13] dma: swiotlb: track pool encryption state and honor DMA_ATTR_CC_SHARED`，目的是让 SWIOTLB 能够感知内存加密状态，并根据设备是否需要解密内存访问来选择合适的 bounce buffer 池。

讨论的关键技术点在于：在 `swiotlb_tbl_map_single()` 中，补丁原本通过 `attrs & DMA_ATTR_CC_SHARED` 和 `force_dma_unencrypted(dev)` 来判断是否需要使用解密池。Mostafa Saleh 提出异议，认为 SWIOTLB 本身不需要感知 `force_dma_unencrypted()`，该信息应由上层调用者（如 dma-direct）根据设备属性统一决定并在调用时传递合适的 DMA 属性（`DMA_ATTR_CC_SHARED`），从而避免在 SWIOTLB 层再做一次 force_dma_unencrypted 的判断。这一意见体现了分层设计中职责分离的考量，避免 SWIOTLB 直接依赖平台级的加密强制策略。

Aneesh Kumar K.V 随后回复确认该逻辑已经更新，并给出了修改后的代码片段（邮件被截断，但可见其注释和部分代码）。从片段中可以看到新的实现思路：设备 SWIOTLB 池必须与设备当前的 DMA 加密要求匹配；若设备需要解密 DMA，则通过未加密池进行反弹并标记为共享；若设备可直接 DMA 到加密内存，则即使原始地址未加密也通过加密池反弹。这意味着 SWIOTLB 将依赖上层传入的 `attrs` 中的 `DMA_ATTR_CC_SHARED` 来区分池的选择，而不再自行检查 `force_dma_unencrypted()`。这一调整的核心是将“解密强制”这一平台策略保留在 DMA 直接映射层，保持了 SWIOTLB 的通用性。

## 参与讨论人员
- Aneesh Kumar K.V (Arm) <aneesh.kumar@kernel.org> — 补丁作者，负责 ARM64 架构相关开发。
- Mostafa Saleh <smostafa@google.com> — 来自 Google，提出审查意见。

## 达成的结论
从有限的邮件片段看，Mostafa 的意见已被 Aneesh 采纳，并体现在代码更新中。Aneesh 明确表示“基于其他邮件线程，目前已更新为……”，说明讨论趋向一致，即从 SWIOTLB 中移除对 `force_dma_unencrypted()` 的直接调用，依赖上层传递合适的标志。但片段未展示后续是否还有其他异议，因此可认为在该具体点上达成了初步共识。

## 下一步改进方向
Aneesh 需要将更新后的实现整合进下一版补丁集（预计 v5），确保调用者（如 `dma_direct_map_page()` 等）正确传递 `DMA_ATTR_CC_SHARED`，并且 SWIOTLB 仅依据该属性选择池。同时可能需要额外测试验证 `force_dma_unencrypted()` 场景下 DMA 属性传递的完整性。

## 新增补丁
邮件中未明确提及新的补丁版本号，但 Aneesh 给出了修改后的 `swiotlb_tbl_map_single()` 注释和逻辑片段，暗示该改动将出现在后续版本中（可能是 v5）。目前仍停留在 v4 讨论阶段，未发布新补丁。

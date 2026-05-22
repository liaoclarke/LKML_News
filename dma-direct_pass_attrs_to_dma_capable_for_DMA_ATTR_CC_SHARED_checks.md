# dma-direct: pass attrs to dma_capable() for DMA_ATTR_CC_SHARED checks

---

## 更新 - 2026-05-22 09:58 UTC

## 核心话题
该补丁是 ARM64 架构机密计算（Confidential Computing）支持系列的一部分，核心目的是让 DMA 能力检查函数 `dma_capable()` 能够感知 `DMA_ATTR_CC_SHARED` 属性。在机密计算环境中（如 ARM CCA、AMD SEV 等），物理内存可能被标记为“私有”（加密）或“共享”（解密）。某些 DMA 设备只能访问共享（未加密）的内存，因此内核在分配 DMA 缓冲区时，必须确保所选地址对设备是可达的。原来的 `dma_capable()` 接口未接收 DMA 属性参数，无法区分加密与未加密的地址，会导致本应被拒绝的私有物理地址被错误地接受，进而引发设备访问故障或数据泄漏。

补丁通过修改 `dma_capable()` 的函数签名，增加 `unsigned long attrs` 参数，使架构或 IOMMU 驱动能依据属性进行更细致的检查。具体变更覆盖了以下文件：
- `include/linux/dma-direct.h`：更新 `dma_capable()` 声明，并在调用时传入属性。同时引入辅助逻辑，当 `attrs` 中包含 `DMA_ATTR_CC_SHARED` 时，即便设备原本要求一致性内存，也允许使用非一致性的共享地址，因为加密属性在这里具有更高优先级。
- `arch/x86/kernel/amd_gart_64.c`：更新 GART IOMMU 的 `need_iommu()` 和 `nonforced_iommu()` 函数，将 `attrs` 透传给 `dma_capable()`。
- `drivers/xen/swiotlb-xen.c` 和 `kernel/dma/swiotlb.c`：在 SWIOTLB 映射过程中，如果选中的 SWIOTLB 池是解密的，则将 `DMA_ATTR_CC_SHARED` 置入 `attrs`，再传递给能力检查，确保后续的判断能看到正确的 DMA 地址属性。
- `kernel/dma/direct.h`：调整相关内联函数的参数传递。

补丁提交者明确指出这是“v5”版本的第 9/20 个补丁，带有 `Tested-by: Jiri Pirko <jiri@nvidia.com>`，说明已有 NVIDIA 人员对该修改进行了测试。从上下文看，该系列旨在为 ARM64 上的机密计算虚拟机提供完整的 DMA 映射支持，本补丁是建立基础框架的关键一环，使 DMA 子系统从底层就能区分共享与私有地址，从而在整个 DMA 映射路径中强制执行正确的地址属性，并为后续的 SWIOTLB 分配、IOMMU 映射等操作提供正确的判断依据。

## 参与讨论人员
- Aneesh Kumar K.V (Arm) <aneesh.kumar@kernel.org> —— 补丁作者
- Jiri Pirko <jiri@nvidia.com> —— 测试者（Tested-by）

## 达成的结论
该邮件仅是一封补丁提交，本线程内未出现后续讨论、反对意见或维护者审阅回复。因此，尚未在讨论中达成任何明确的结论或共识。补丁作为系列的一部分被发布，其结论需要等待整体系列的审阅结果。

## 下一步改进方向
由于当前线程没有收到审查反馈，下一步需要：
1. 社区维护者（如 DMA 映射子系统和 ARM64 架构的维护者）对补丁进行功能正确性与代码风格的审查。
2. 确认所有调用 `dma_capable()` 的路径都已正确处理 `attrs` 的传递，避免遗漏其他 IOMMU 驱动（例如 Intel VT-d，AMD IOMMU 等）。
3. 在更广泛的硬件平台上进行回归测试，特别是涉及加密内存与 SWIOTLB 交互的场景。
4. 可能需要根据后续补丁的依赖关系进行调整，确保系列内各补丁能顺利合并。

## 新增补丁
- 本邮件即为新增补丁：`[PATCH v5 09/20] dma-direct: pass attrs to dma_capable() for DMA_ATTR_CC_SHARED checks`（v5 版本，系列第 9 补丁）。该版本相较于之前版本的主要变化未在邮件中直接说明，但从上下文推断，v5 可能整合了测试反馈并调整了某些属性的传递逻辑。

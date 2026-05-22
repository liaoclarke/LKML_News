# dma: swiotlb: pass mapping attributes by reference

---

## 更新 - 2026-05-22 09:58 UTC

## 核心话题
该邮件是 Linux 内核 ARM64 架构相关的 DMA/SWIOTLB 重构补丁系列（v5）中的第 06/20 号补丁，提交者为来自 Arm 公司的 Aneesh Kumar K.V。补丁的核心是将 `swiotlb_tbl_map_single()` 函数的 DMA 映射属性参数从**按值传递**改为**按引用传递**（即传递 `unsigned long *` 而非 `unsigned long`），并同步更新所有直接调用点。补丁说明明确指出，这是一项**无功能变更**的预备性工作，目的是为后续补丁中“根据所选 SWIOTLB 内存池更新属性”的需求提供便利。将签名变更独立出来，可以让后续补丁的审查更为聚焦。

从技术细节看，修改涉及四个文件：
- `include/linux/swiotlb.h`：函数声明中将 `attrs` 改为 `*attrs`。
- `kernel/dma/swiotlb.c`：函数定义中将 `attrs` 改为 `*attrs`，内部对 `attrs` 的访问随之调整为解引用或取地址。
- `drivers/iommu/dma-iommu.c`：调用点 `iommu_dma_map_swiotlb()` 中将实参 `attrs` 改为 `&attrs`。
- `drivers/xen/swiotlb-xen.c`：调用点 `xen_swiotlb_map_phys()` 中将实参 `attrs` 改为 `&attrs`。

该变更的动机是，后续补丁需要在 `swiotlb_tbl_map_single()` 内部根据所选择的 SWIOTLB 池的类型（例如是否与 Restricted DMA 相关）动态调整 DMA 属性（如是否为 `DMA_ATTR_SKIP_CPU_SYNC` 等），以支持更精细的权限控制或缓存一致性策略。由于 C 语言按值传递无法让被调用者修改调用者的变量，因此需要改为指针传递。补丁保证当前行为完全不变，只是为未来的功能性变更打好地基。这种重构在内核中十分常见，体现了将逻辑调整与接口变更解耦的良好实践。

## 参与讨论人员
- Aneesh Kumar K.V (Arm) -- 补丁提交者，来自 Arm 公司。

（邮件线索中仅有该单人提交，未出现回复或讨论）

## 达成的结论
由于该邮件仅是一个补丁提交，对应讨论串尚未产生回复，因此**未达成任何共识**。补丁本身表达了提交者的设计意图，即先完成接口调整，后续补丁再利用引用传递的特性修改 DMA 属性。社区是否接受该 API 变更方向，需等待维护者及其他开发者的审查意见。

## 下一步改进方向
1. **社区审查**：等待 DMA/SWIOTLB 子系统维护者（如 Christoph Hellwig、Konrad Rzeszutek Wilk 等）及其他 ARM64/iommu 相关人员对此次接口变更的合理性进行 Review，给出 Acked-by 或提出修改意见。
2. **全系列上下文**：该补丁为 v5 系列 20 个补丁中的第 6 个，需要结合后续补丁（尤其是利用该引用修改属性的补丁）一起理解整体设计，确保预备性变更的确有后续消费，避免孤立的 API 改动。
3. **测试**：虽然声称无功能变化，但调用点改动后仍需通过 SWIOTLB 相关测试（如 Xen 下的 DMA、受限 DMA 场景等），确保没有引入编译警告或运行时行为意外改变。
4. **更新文档（如需）**：若最终接口被接受，可能需要同步更新内核 DMA-API 文档或相关注释，说明属性传递方式的变化。

## 新增补丁
本邮件即为补丁提交，版本为 **PATCH v5 06/20**，是第五版系列补丁中的一部分。该补丁在此线索中未出现更新的修订版本。

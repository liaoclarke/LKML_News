# iommu/arm-smmu-v3: Detect ARM_SMMU_OPT_KDUMP_ADOPT in probe()

---

## 更新 - 2026-05-20 10:03 UTC

## 核心话题
该补丁针对 ARM SMMUv3 驱动在 kdump 场景下对崩溃内核流表的处理方式进行了细化。原本在补丁 b63b3439b856（“iommu/arm-smmu-v3: Abort all transactions if SMMU is enabled in kdump kernel”）中，当 kdump 内核发现 SMMU 已经处于使能状态时，无条件地终止所有待处理的事务，以防止设备 DMA 干扰新内核。但这种方式过于粗暴，导致一些本可继续进行的 DMA 操作也被强行中止。本补丁引入了 `ARM_SMMU_OPT_KDUMP_ADOPT` 选项，允许 kdump 内核在满足一定条件时，直接“采纳”（adopt）崩溃内核已建立的流表，而非重置 SMMU。这样既能避免重置带来的 DMA 中断，又能最大限度地保持设备 I/O 的连续性。

检测逻辑被放置于 `arm_smmu_device_hw_probe()` 中，早于 `arm_smmu_init_structures()`，这是自然的，因为需要在初始化阶段就决定是否沿用旧的流表。具体条件包括：
1. SMMU 必须已使能（CR0_SMMUEN 置位），否则无流表可采纳。
2. SMMU 必须支持硬件一致性（`ARM_SMMU_FEAT_COHERENCY`），因为后续需通过 `memremap` 以写回（WB）方式映射旧的流表内存；若为非一致性 SMMU，则回退到原有行为，即重置并阻止所有 DMA。
3. SMMU 不能处于服务失败模式（Service Failure Mode, SFM），如果检测到 GERROR 中 SFM 错误标志，则强制重置，以确保安全性。

这一修改完善了 kdump 下 SMMU 的处理策略：从“一律阻断”升级为“有条件沿用”，减少了 kdump 过程中不必要的 I/O 中断，同时保留了必要的安全边界。

## 参与讨论人员
- Nicolin Chen (nvidia.com) —— 补丁作者
- Kevin Tian (intel.com) —— 审阅者（Reviewed-by）
- Jason Gunthorpe (nvidia.com) —— 审阅者（Reviewed-by）

（由于邮件线程仅截取此一封，可能还有未列出的讨论者）

## 达成的结论
该补丁 v6 已获得 Kevin Tian 和 Jason Gunthorpe 的 Reviewed-by 标签，表明核心开发者认可该方案，共识已达成。补丁被视为对之前 kdump 行为的修复，将被纳入主线内核，并计划合入 stable 内核 v6.12+。

## 下一步改进方向
- 补丁需要实际合入 Linux 内核主线（预计通过 iommu 维护者提交）。
- 需要回溯到 stable 内核 v6.12 及更高版本。
- 虽然代码层面已对非一致性 SMMU 和 SFM 情况进行了回退处理，但可能需要更多测试验证这些回退路径的健壮性，特别是在真实硬件 kdump 场景下。

## 新增补丁
本邮件为系列补丁 [PATCH rc v6 7/7] 的最后一版。该版本在 v6 中首次引入此 kdump 检测逻辑，未在之前版本出现（或为系列重构后的新增部分）。变更内容为在 `arm_smmu_device_hw_probe()` 中增加 31 行新函数 `arm_smmu_device_hw_probe_kdump()`，用以设置 `ARM_SMMU_OPT_KDUMP_ADOPT` 选项。

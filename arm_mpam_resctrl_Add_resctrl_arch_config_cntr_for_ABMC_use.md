# arm_mpam: resctrl: Add resctrl_arch_config_cntr() for ABMC use

---

## 更新 - 2026-05-20 22:24 UTC

## 核心话题
该邮件是 Linux 内核 arm_mpam 子系统关于 resctrl 架构计数配置函数 `resctrl_arch_config_cntr()` 的补丁实现，属于 ABMC（Assigned Bandwidth Monitoring Counters，可分配带宽监控计数器）功能的支持工作。

补丁由 James Morse 撰写，Ben Horgan 提交，版本为 v4。在之前的版本中，MPAM（Memory Partitioning and Monitoring，内存分区与监控）架构对该函数的实现为空壳，本补丁为其填充了实际功能：通过辅助函数 `__config_cntr` 动态更新监控结构 `mpam_resctrl_mon` 中的 `mbwu_idx_to_mon[]` 数组，从而改变计数器 ID 与 CLOSID/RMID 对之间的映射关系。

技术核心在于：
- 该函数被 resctrl 核心层调用，用于将某个具体计数器（`cntr_id`）分配给或解除与某一 CLOSID（类控制标识符）和 RMID（资源监控标识符）组合的绑定（`assign` 参数控制）。
- 在 MPAM 实现中，映射是通过数组 `mbwu_idx_to_mon[]` 维护的，其中 `mbwu_idx` 由 `resctrl_arch_rmid_idx_encode(closid, rmid)` 编码生成。
- 因 MPAM 支持 CDP（Cache Data Path，缓存数据路径）特性，即不同缓存分配类型（如数据、指令）可能独立配置，计数器索引需要根据 `cdp_type` 通过 `resctrl_get_config_index()` 进行转换，确保在三种配置方式下正确运算。实现中包含了 `WARN_ON_ONCE(mon_idx >= l3_num_allocated_mbwu)` 边界检查。
- 补丁还提及 `mbm_event` 模式，这是 ABMC 功能的一种监控事件工作模式。

变更日志中提到了自 rfc 以来的变化：在提交消息中明确提及 mbm_event 模式；自 v3 版本集的修改为修复了 Sashiko 指出的警告边界问题。补丁获得了 Jonathan Cameron 的 Reviewed-by 签章。

## 参与讨论人员
- **Ben Horgan** (arm.com) — 补丁发送者、维护者之一。
- **James Morse** (arm.com) — 补丁原始作者。
- **Jonathan Cameron** (huawei.com) — 评审者，提供了 Reviewed-by。
- **Sashiko** — 在变更日志中提及，指出了先前版本中的警告边界问题（可能为另一位审阅者，全名未详细给出）。

## 达成的结论
从提供的邮件片段看，未能看到后续讨论，不构成多轮辩论。当前状态仅为补丁 v4 的单方面提交，包含了此前评审意见的修正。因此，没有就设计或实现产生分歧，也未达成明确的终结合意，只是补丁迭代中的一次正常发布。

## 下一步改进方向
下一步需要：
- 等待社区其他维护者（如 resctrl 子系统和 ARM64 架构维护者）进一步审查。
- 确认修复的边界检查是否能通过所有测试场景，尤其是 CDP 配置下的边界情况。
- 将该补丁与其所在系列的其他补丁（如 1/5, 2/5, 4/5, 5/5）一同整合，通过完整的 ARM MPAM ABMC 功能测试。
- 如果没有新的反对意见，预计该补丁将在下一个合并窗口中被合入。

## 新增补丁
本邮件即为 v4 版本补丁 [PATCH v4 3/5]。相较于 v3 的改动：
- 在提交说明中补充了“mbm_event mode”的提及，以明确使用场景。
- 修复了 Sashiko 审阅时发现的边界警告不严谨问题（具体在 `WARN_ON_ONCE` 条件或其前置逻辑上，细节未展开）。

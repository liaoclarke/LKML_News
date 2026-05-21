# arm_mpam: resctrl: Add resctrl_arch_cntr_read() & resctrl_arch_reset_cntr()

---

## 更新 - 2026-05-20 22:24 UTC

## 核心话题
本补丁是 `arm_mpam` 在 resctrl 框架中继续完善监控支持的一部分，专门针对“ABMC仿真模式”（mbm_event模式）下的内存带宽利用率（MBWU）计数器操作，添加或重实现 `resctrl_arch_cntr_read()` 与 `resctrl_arch_reset_cntr()` 两个架构钩子。  
补丁消息明确指出，之前的代码中这两个函数要么是空实现，要么直接返回 `-EOPNOTSUPP`，不支持 MBWU 事件的读取与重置。现在为了使用预分配的监控计数器（`USE_PREALLOCATED_IDX`），需要在 `__read_mon()` 中实现 mbwu 索引的解析，通过 `resctrl_arch_rmid_idx_encode(closid, rmid)` 得到 `mbwu_idx`，再映射到真正的监控索引 `mon_idx`；若映射失败（`mon_idx == -1`）则返回错误。同时，为支持 CDP（代码与数据剖面，`cdp_enabled` 为真），硬件计数器需要区分代码和数据的独立计数器。  
补丁的 diff 显示，原先的 `resctrl_arch_reset_cntr()` 和 `resctrl_arch_cntr_read()` 两个空定义被移除，并在 `__read_mon()` 函数中增加了 `USE_PRE_ALLOCATED` 的处理分支。由于邮件被截断，完整实现未完全展示，但其核心逻辑是：当监控类型为预分配时，利用 `closid` 和 `rmid` 计算出 mbwu 索引，然后在 `mon->mbwu_idx_to_mon[]` 表中查找对应的硬件监控索引，如果找到则使用它进行读取，否则返回 `-E`（可能是 `-EINVAL` 或 `-ENOENT`，原文被截断，只显示了 `-E`）。该补丁由 James Morse 编写，Jonathan Cameron 提供了审核标签（Reviewed-by），Ben Horgan 负责提交。

## 参与讨论人员
- **Ben Horgan** (Arm) — 补丁的发送者与 Signed-off-by
- **James Morse** (Arm) — 补丁的原始作者与 Signed-off-by
- **Jonathan Cameron** (Huawei) — Reviewed-by 提供者

（当前邮件中未见其他回复者，仅包含补丁提交者与审核者）

## 达成的结论
该线程仅包含单一补丁提交邮件，未出现后续讨论或反对意见。因此可以认为补丁已经在开发者内部达成一致（已获得审核标签），目前处于向社区公开评审阶段，尚未发现异议。由于邮件内容不全，无法断定是否最终被接受，但提交本身代表了向 resctrl/MPAM 子系统集成 MBWU 计数器支持的最新进展。

## 下一步改进方向
- 补丁需要经过更广泛的社区评审（如 x86 维护者或 resctrl 维护者的审查），确保 `USE_PREALLOCATED_IDX` 相关的设计与现有 resctrl 架构兼容。
- 截断的 diff 结尾 `return -E` 需要补齐为正确的 errno（可能是 `-EINVAL` 或 `-ENOENT`），并确保在处理 mbwu_idx 越界时的错误处理完整。
- 有可能需要补充对应的 `resctrl_arch_reset_cntr()` 具体实现，因为补丁标题提及该函数但 diff 中未显示部分实现（邮件截断可能隐藏了后续内容）。
- 测试要求：覆盖 ABMC 仿真模式、CDP 开启/关闭场景、以及 `mbwu_idx_to_mon` 映射失败的异常路径。

## 新增补丁
此邮件提交的是 **v4** 版本的补丁，属于一个 5 补丁系列的第 4 个。该版本相对于 v3 的变更包括：使用 `USE_PREALLOCATED_IDX`，明确在 `cdp_enabled` 时需为代码和数据分配独立硬件计数器。邮件中未再次发布更新版本。

# arm_mpam: resctrl: Pre-allocate assignable monitors

---

## 更新 - 2026-05-20 22:24 UTC

## 核心话题
本邮件是Ben Horgan提交的针对Linux内核ARM64架构MPAM（Memory Partitioning and Monitoring）resctrl子系统的补丁v4系列的第2个补丁。核心目标是为MPAM的resctrl驱动实现内存带宽监测器（monitor）的预分配，以模拟ABMC（Assignable Bandwidth Monitoring Counters）功能，也就是resctrl框架中的`mbm_event`模式。

当前补丁的动机在于：MPAM硬件有能力通过让内存带宽监测器变为“可分配”来模拟ABMC。为了简化未来对MPAM的“每个监测器独立事件配置”的支持，该补丁强制要求即使系统中存在足够数量的内存带宽监测器，也始终使用`mbm_event`模式，而非默认的`default`模式。只有在`mbm_event`模式下，resctrl才会提供针对每个监测器的事件配置接口，这为MPAM实现更细粒度的事件配置（例如不同的带宽类型）铺平了道路。目前，唯一支持的事件是`mbm_total_event`，且没有带宽类型配置。驱动仍然会在`mbm_assign_mode`文件中显示为`default`，当系统不支持内存带宽监控时。

补丁的具体实现包括：
- 从驱动中预分配监测器，并将它们映射到resctrl所需的任意控制/监视组（control/monitor group）。为此，新增了一个以resctrl的`cntr_id`为索引的数组，用于存放监测器的值。
- 当启用CDP（Code and Data Prioritization，代码与数据优先级分离）时，每个监视组需要两个监测器（分别用于代码和数据），因此可用监测器数量减半。如果平台只有一个监测器，那么在启用CDP后将变得不可用（零个监测器），补丁中处理了这种降级情况。
- 补丁描述中明确写道：“Rather than supporting the 'default' mbm_assign_mode always use 'mbm_event' mode even if there are sufficient memory bandwidth monitors.” 这体现了设计决策的彻底转向，不再尝试根据资源情况动态切换模式，而是强制单一模式以保证接口一致性。
- 此外，还引入了若干辅助函数，并改进了错误处理和内存分配方式（如使用`kvmalloc_obj`）。

该补丁是“arm_mpam: resctrl”系列的一部分，由James Morse与Ben Horgan共同开发。补丁的版本演进（从RFC v1到v4）中修复了许多问题，例如不再将`mon->assigned_counters`设为错误指针、修正了`mpam_resctrl_teardown_mon()`函数、去除了对自由运行（free running）模式的检查、分离了清理分配等。这也反映出该方案经过多轮打磨，已经趋于稳定。

## 参与讨论人员
- Ben Horgan (Arm公司)
- James Morse (Arm公司)（共同开发者）
- （变更日志中提及了Shaopeng和Sashiko在历史版本中提供过反馈，但未出现在本邮件的直接讨论中）

## 达成的结论
本邮件为单独的一个补丁提交，邮件列表中并未出现其他参与者的回复或讨论，因此在该线程内未形成任何明确的共识或结论。该补丁目前处于待审查状态。

## 下一步改进方向
- 等待社区对补丁的审查和反馈，特别是关于强制`mbm_event`模式的设计是否合理。
- 可能需要进一步阐述对“per-monitor event configuration”未来扩展的支持路径，以及在CDP情况下降级处理的稳健性。
- 后续可能需要进行更广泛的测试，覆盖不同MPAM硬件配置以及与其他resctrl系列补丁的集成。
- 该补丁作为系列的一部分，其集成需要依赖整个补丁系列的审查进展。

## 新增补丁
本邮件中仅包含v4版本的补丁（PATCH v4 2/5），没有后续的新版本提交。变更日志中详细记录了自RFC v1以来的所有改动，包括：
- 即使有足够计数器也启用abmc
- 引入来自已删除的“自由运行”提交的帮助函数
- 处理使用CDP后计数器为零的情况
- 设置配置位
- 使用`kmalloc_objs`和`kvmalloc_obj`优化内存分配
- 配置`mbm_cntr_configurable`和`mbm_cntr_assign_fixed`字段
- 修复`mpam_resctrl_teardown_mon()`中的NULL检查问题等。

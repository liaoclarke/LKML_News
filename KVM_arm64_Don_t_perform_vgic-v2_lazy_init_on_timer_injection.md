# KVM: arm64: Don't perform vgic-v2 lazy init on timer injection

---

## 更新 - 2026-05-20 11:26 UTC

## 核心话题
本讨论围绕一个针对ARM64架构KVM的补丁集，主题是“KVM: arm64: Don't perform vgic-v2 lazy init on timer injection”（避免在定时器注入时执行vgic-v2的惰性初始化）。该补丁集由Marc Zyngier发布（v3版本），旨在修复一个在非抢占式上下文（non-preemptible context）中意外触发vgic-v2初始化的问题。vgic-v2的lazy init机制原本是为了延迟虚拟中断控制器的初始化直至首次真正需要，但如果在中断注入路径（例如定时器触发）且当前上下文不可抢占时触发初始化，可能导致内核警告甚至死锁。

Marc在第三次迭代中做了多项改进：
- 将定时器相关的`kvm_timer_should_fire()`和`kvm_timer_irq_can_fire()`重命名为更贴切的`kvm_timer_pending()`和`kvm_timer_enabled()`，以准确反映其语义（补丁1）。
- 简化了用户态关于中断状态的通知机制（补丁2）。
- 移除了每定时器独立维护的irq level缓存（补丁3），并进一步移除了PMU中断级别的缓存（补丁4），消除了隐藏的状态冗余。
- 核心修复在补丁5和6：在运行循环之外的注入路径上，强制进行vgic初始化（缓解irqfd慢路径等问题），并最终确保在发生内核内部中断注入时不会触发vgic初始化，从而彻底规避非抢占上下文初始化的风险。

Oliver Upton在回复中首先指出了一个拼写错误：最后一补丁的变更日志首行把“now”误写为“how”，但表示懒得为此重发邮件，随后给出了`Reviewed-by`标签。

## 参与讨论人员
- **Marc Zyngier** (maz@kernel.org) — 补丁作者，很可能来自Google或Arm，负责KVM arm64维护。
- **Oliver Upton** (oupton@kernel.org) — 审查者，同样活跃于KVM arm64领域，可能来自Google。

## 达成的结论
已达成明确共识：Oliver Upton认可整个v3补丁系列的技术设计，给出了“Reviewed-by: Oliver Upton <oupton@kernel.org>”。仅有一个非功能性笔误（s/how/now/）被指出，但未构成阻碍，因此可以认为补丁集已获得必要审查确认，准备进入合并阶段。

## 下一步改进方向
- 由维护者在合入前将最后的补丁变更日志中“s/how/now/”的拼写修正，或在应用补丁时自动修复。
- 等待将v3系列合入KVM arm64的下一开发分支（如`next`），并随后进入主线。
- 无需额外的代码改动或重新发送系列，除非有其他开发者提出异议。

## 新增补丁
在本邮件线程中未发布新的补丁版本。当前讨论围绕的是v3版本，无v4或增量修复补丁提交。

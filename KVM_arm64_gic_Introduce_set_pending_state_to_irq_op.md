# KVM: arm64: gic: Introduce set_pending_state() to irq_op

---

## 更新 - 2026-05-21 14:58 UTC

## 核心话题
该邮件是 Sascha Bischoff 提交的 KVM arm64 GIC 中断处理改进补丁（v2 系列第 28/39），旨在为 `irq_ops` 结构体增加一个名为 `set_pending_state()` 的新函数指针。其核心技术动机在于：在 GICv5 等新一代中断控制器中，SPI（共享外设中断）和 LPI（局部外设中断）的部分生命周期可由硬件直接管理，pending 状态不再仅凭 VGIC 的影子状态（shadow state）来表示，而是需要直接与硬件同步。当前架构中，`kvm_vgic_inject_irq()` 在更新 VGIC 内部的 `pending_latch` 后，并没有通知后端硬件生效，这会导致硬件直接管理的 pending 状态与 VGIC 影子状态脱节。

为此，补丁在 `include/kvm/arm_vgic.h` 的 `irq_ops` 中新增 `bool (*set_pending_state)(struct kvm_vcpu *vcpu, struct vgic_irq *irq)` 回调，使得在 VGIC 影子 pending 状态变更后，可以立即调用该回调将更新镜像到硬件中。在 `kvm_vgic_inject_irq()` 中，新增逻辑检查 `irq->ops` 和该函数指针是否设置，若设置则调用并捕获错误（`WARN_ON_ONCE`），确保硬件状态与影子状态一致性。一般情况（无 ops 或未设置该指针）则无任何额外开销，不影响现有流程。

关键引用包括：“There are times, such as with GICv5 SPIs and LPIs, where the hardware itself manages parts of the interrupt lifecycle. This means that pending state can be directly communicated to the hardware instead of being represented only in the VGIC shadow state.” 以及 “The intent is for this to be used after the VGIC shadow pending state has changed, allowing the backend to mirror the updated state into hardware.” 这些片段明确指出了新接口的设计目标与适用场景。

## 参与讨论人员
- Sascha Bischoff (Arm)，补丁提交者

## 达成的结论
该邮件仅为补丁提交，未出现后续讨论、评审意见或反对声音，因此尚未达成任何社区共识。该补丁作为初步实现方案，需等待其他维护者或开发者的审阅与反馈。

## 下一步改进方向
1.  需要社区评审者对新增接口的必要性、命名及实现细节进行审查，确认其与现有 VGIC 架构的兼容性。
2.  需要明确 `set_pending_state()` 回调的具体实现（本补丁未提供），并可能补充配套的文档或测试用例，以验证对 GICv5 及未来硬件的支持。
3.  考虑该回调返回 `bool` 的含义（当前表示成功与否），需讨论错误处理路径（如 `WARN_ON_ONCE` 后是否应回退状态或采取其他恢复措施）。
4.  评估是否有其他中断注入路径（如来自设备直通或用户态注入）也需要调用该回调，以确保完整性。

## 新增补丁
本邮件中仅包含一个补丁：
- `[PATCH v2 28/39] KVM: arm64: gic: Introduce set_pending_state() to irq_op`  
  该补丁在 `irq_ops` 中新增 `set_pending_state` 回调，并在 `kvm_vgic_inject_irq()` 中调用，为后续硬件直接管理 pending 状态提供基础设施。

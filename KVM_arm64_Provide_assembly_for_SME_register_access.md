# KVM: arm64: Provide assembly for SME register access

---

## 更新 - 2026-05-21 15:51 UTC

## 核心话题
本邮件线程围绕为 KVM hypervisor 提供 SME 寄存器访问的汇编函数展开讨论。原补丁（v10 19/30）由 Mark Brown 提交，在 `arch/arm64/kvm/hyp/fpsimd.S` 中添加了 `__sme_save_state` 和 `__sme_restore_state` 函数，用于在 hypervisor 中保存和恢复 guest 的 ZA 与 ZT 状态。这使得 KVM 能够支持 SME 上下文切换，是对 arm64 SME 虚拟化支持的一部分。

Mark Rutland 对此提出了架构层面的异议。他指出虽然当前这个补丁改动不大，但不应继续在主流内核与 KVM hyp 代码之间重复低层的状态保存/恢复逻辑。他认为这种重复不仅增加了维护负担，也为后续的特性支持埋下隐患。因此，他专门发布了一个前置清理系列（见新增补丁部分），旨在统一 FPSIMD/SVE 的保存/恢复接口，从而彻底避免 KVM hyp 需要单独复制这些汇编函数。

核心论点是：“I don't think we should continue to duplicate the low level save/restore routines between the main kernel and KVM hyp code.” Mark Rutland 强调，在进行 KVM SME 支持之前，应当先完成该清理工作，并将 KVM 的 SME 支持建立在这个统一的接口之上。他同时表明这一方向需要获得 KVM/arm64 维护者 Marc Zyngier 和 Oliver Upton 的同意。

## 参与讨论人员
- Mark Rutland (Arm)
- Mark Brown (提交者)
- Marc Zyngier (被提及，KVM/arm64 维护者)
- Oliver Upton (被提及，KVM/arm64 维护者)

## 达成的结论
本次讨论尚未达成最终共识，但提出了一个明确的前置依赖方向。Mark Rutland 建议在 KVM SME 支持合入之前，先应用其清理系列以避免代码重复。这将需要得到 KVM 维护者的认可，讨论中并无反对意见，目前等待维护者确认。

## 下一步改进方向
1. 需要 Marc Zyngier 和 Oliver Upton 对 Mark Rutland 提出的清理系列表态，确认该重构是 KVM SME 支持的必要前置。
2. 若清理系列获得合入，Mark Brown 需要将 KVM SME 支持补丁 rebase 到该系列之上，移除 hyp 中重复的汇编函数，转而使用统一接口。
3. 后续可能需要重新测试并提交更新后的 KVM SME 补丁版本。

## 新增补丁
Mark Rutland 在本邮件中引用了一个新的补丁系列，用于统一低层保存/恢复逻辑，间接影响本补丁：
- **系列链接**：https://lore.kernel.org/linux-arm-kernel/20260521132556.584676-1-mark.rutland@arm.com/
- **变化简述**：该系列清理了 FPSIMD/SVE 状态保存/恢复在主流内核与 KVM hyp 间的重复代码，为避免本次 SME hyp 汇编函数的重复提供了基础。当前邮件中并未发布 Mark Brown 补丁的新版本。

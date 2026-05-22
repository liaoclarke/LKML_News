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

---

## 更新 - 2026-05-22 06:52 UTC

## 核心话题
该邮件线程围绕 ARM64 KVM 中支持 SME（Streaming SVE Mode）扩展而引入的汇编状态保存/恢复代码展开。原始补丁（PATCH v10 19/30）为 hypervisor 提供了在宿主与客户机之间保存/恢复 ZA 和 ZT 寄存器的专用汇编函数，通过修改 `arch/arm64/kvm/hyp/fpsimd.S` 实现。这一做法是在现有 FPSIMD/SVE 上下文的低层次处理之上继续叠加 SME 支持。

Mark Rutland 对此提出反对，认为不应继续在主线内核与 KVM hyp 代码之间重复维护低层次的保存/恢复例程。他指出，这种重复会导致代码膨胀、维护困难，且已经使整个 FP/SVE 子系统过于复杂，难以审计。为此，他主动发送了一个重构系列（链接在手邮件中提供），旨在消除重复，并建议先完成该清理工作，再在其上构建 KVM SME 支持。

Marc Zyngier 明确表示“绝对”同意 Mark Rutland 的观点，并给出了进一步的动机：整个 FP/SVE 代码“仍然过于复杂，充斥着晦涩的结构，难以审计”，因此非常希望在添加另一个层次（SME）之前先进行清理。他快速浏览了 KVM 相关的 SME 补丁，认为没有过分离谱的地方，这部分代码有机会进入 6.2 内核（邮戳给出的 7.2 可能是笔误或发布版本代号），并计划近期再次审阅。这一对话体现了维护者对于代码健康度的坚持，以及对避免技术债务在扩展特性时不断累积的关注。

核心争论点在于：是直接在现有 FP/SVE 汇编基础设施上“打补丁”式地增加 SME 支持，还是先重构基础设施以消除重复、提高可维护性，再引入新功能。两位主要维护者最终达成一致，选择了后一种长远更优的方案。

## 参与讨论人员
- Marc Zyngier (maz@kernel.org) — KVM/arm64 维护者
- Mark Rutland (mark.rutland@arm.com) — ARM 架构维护者
- Mark Brown (broonie@kernel.org) — 原始补丁作者（在本邮件事中被回复，未直接发言）

## 达成的结论
达成明确共识。Mark Rutland 提出的“先清理 FP/SVE 重复代码，再在其上构建 KVM SME 支持”的方案得到 Marc Zyngier 的完全认可。双方一致决定推迟当前 SME 汇编辅助函数的合并，等待清理系列被接纳并合并后，再基于清理后的代码提交 KVM SME 支持。不存在任何分歧。

## 下一步改进方向
1. **代码清理合并**：推进 Mark Rutland 的清理系列（`https://lore.kernel.org/linux-arm-kernel/20260521132556.584676-1-mark.rutland@arm.com/`）的审阅与合并，消除 FPSIMD/SVE 状态保存/恢复在 hyp 与内核之间的重复。
2. **KVM SME 补丁重组**：Mark Brown 需要在清理后的基础上重新整理 KVM SME 相关补丁，删除不再需要的汇编重复代码，并确保新实现复用统一的结构。
3. **维护者审阅**：Marc Zyngier 计划很快重新审阅 KVM 特化的 SME 补丁（非汇编部分），确认其合理性，为后续合并做好准备。
4. **测试验证**：在清理系列和重构后的 SME 支持合并后，需对 SME 主机与客户机场景进行全面回归测试，确保状态保存/恢复的正确性。

## 新增补丁
在此邮件线程中，并未发布原始补丁的新版本。但 Mark Rutland 给出了一个前置重构系列：
- 系列链接：https://lore.kernel.org/linux-arm-kernel/20260521132556.584676-1-mark.rutland@arm.com/
该系列旨在清理低层次 FP/SVE 保存/恢复的重复代码，是后续 KVM SME 支持的前提。因此，下一步工作的直接依赖变为该清理系列的接受与合并。

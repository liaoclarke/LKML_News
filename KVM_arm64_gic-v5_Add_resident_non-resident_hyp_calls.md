# KVM: arm64: gic-v5: Add resident/non-resident hyp calls

---

## 更新 - 2026-05-21 14:54 UTC

## 核心话题
该补丁讨论的是在为 KVM/arm64 引入 GICv5 支持的过程中，增加 **VPE（虚拟处理器）驻留（resident）与非驻留（non-resident）的 hypercall 机制**。GICv5 中断控制器中引入了一个核心概念——**中断路由子系统（IRS, Interrupt Routing System）**，它可以同时处理 SPI 和 LPI 中断，并通过 VPE 驻留状态来决定是否将该 VPE（或 VM）作为最高优先级待处理中断（HPPI）来参与中断选择。补丁明确指出：“**When the VPE is resident, the IRS is allowed to select interrupts that target that VPE... as the HPPI**”。当 VPE 不处于运行状态时，必须将其标记为非驻留，从而让 IRS 停止为其进行 HPPI 选择，避免中断被错误地投递到未运行的 VPE。

为实现这一控制，补丁新增了两个 hyp 调用：一个用于让 VPE 变为驻留（通过设置 `ICH_CONTEXTR_EL2.V` 并写入有效的 VM 和 VPE ID），另一个用于让其变为非驻留（使 `ICH_CONTEXTR_EL2` 无效）。切换过程通过写 `ICH_CONTEXTR_EL2` 寄存器完成，其中驻留写入会将 VPE 相关信息告知硬件 IRS，而非驻留写入则会清除这些信息，使 IRS 忽略该 VPE。

补丁同时扩展了原有的 `vgic_v5_load()` 和 `vgic_v5_put()` 函数，在 KVM 的 VPE 上下文加载/卸载时分别调用驻留/非驻留 hyp call，使得**整个 VPE 从加载到卸载的区间内都被视为驻留**。这在语义上保证了只有正在运行的 VPE 才会响应 GICv5 的中断。

此外，补丁还处理了一种异常情况：当尝试将 VPE 置为驻留时，会检查 `ICH_CONTEXTR_EL2.F` 位，如果该位被置位，代表发生“驻留故障”（residency fault）。这种故障通常是因为 VM 或 VPE 配置存在根本性错误，补丁将其视为不可恢复的错误，会输出警告并将 VM 标记为“死亡”，以防止进一步损坏。

该补丁是 v2 系列 39 个补丁中的第 15 个，目的是为 GICv5 的虚拟化支持奠定基础，让 VPE 的中断路由行为能够与 VPE 的实际调度状态同步，这也是实现 GICv5 全功能虚拟化的必要步骤。

## 参与讨论人员
- **Sascha Bischoff** (Arm) —— 补丁提交者，目前唯一的讨论参与者。

## 达成的结论
由于邮件线程中暂未出现其他维护者或开发者的回复，**尚未形成任何结论**。补丁处于待审查状态，等待社区反馈，尤其是 KVM/arm64 维护者（如 Marc Zyngier）的技术审查。

## 下一步改进方向
1. 需要 KVM/arm64 维护者或其他相关开发者对补丁的设计进行审查，特别是 hypercall 的接口定义、`ICH_CONTEXTR_EL2` 操作的安全性以及驻留故障的处理策略。
2. 可能需要补充更多的注释或文档，解释驻留和非驻留操作与 VPE 生命周期管理之间的精确语义。
3. 在实际硬件或模型上验证驻留切换对 GICv5 中断投递的影响，并进行性能与正确性测试。
4. 如果审查中发现设计不合理，可能需要重新组织代码结构或调整 hypercall 的调用时机。

## 新增补丁
本次邮件中提交的是 **v2 版本**补丁，标题为 `[PATCH v2 15/39] KVM: arm64: gic-v5: Add resident/non-resident hyp calls`。本线程内未出现更新的补丁版本。

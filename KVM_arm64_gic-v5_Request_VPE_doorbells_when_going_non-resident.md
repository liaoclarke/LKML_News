# KVM: arm64: gic-v5: Request VPE doorbells when going non-resident

---

## 更新 - 2026-05-21 14:06 UTC

## 核心话题
本讨论围绕 KVM/arm64 中 GICv5 中断控制器的虚拟化，具体聚焦于 **VPE（虚拟处理单元）在退出驻留（non‑resident）时的门铃（Doorbell）请求机制**。补丁作者 Sascha Bischoff 希望在 `vgic_v5_put` 函数中，当虚拟 CPU 进入 WFI 状态并被切换下线时，通过 ITS 的 In‑Review Service（IRS）为对应 VPE 注册一个门铃信号，从而在后续有 SPI/LPI 中断挂起时，硬件能直接发送该 VPE 的门铃唤醒 KVM，避免纯软件轮询带来的延迟与功耗。

技术要点如下：
- **请求条件**：仅当 vCPU 的标志 `IN_WFI` 被置位时才会请求门铃。如果 vCPU 只是短暂退出（未进入 WFI），则不需要门铃，因为预期其会立即重新调度，频繁的门铃开销反而有害。
- **优先级过滤（DBPM）**：请求门铃时需计算 DoorBell Priority Mask（DBPM）。该掩码保证只有当挂起中断的优先级足够高时，硬件才会真正触发门铃。这避免了唤醒一个根本无法处理该中断（当前优先级掩码 PMR 已屏蔽）的 VPE，减少无意义的上下文切换。
- **实现位置**：代码修改位于 `arch/arm64/kvm/vgic/vgic-v5.c` 的 `vgic_v5_put` 函数，原有路径已有对非驻留情况的处理，新补丁插入门铃请求逻辑。

邮件片段中明确说明了设计动机：
> “When a VPE is made non‑resident and is entering WFI, a doorbell should be requested for the VPE. This allows the VPE to be easily woken once an SPI/LPI interrupt is pending for it. […] Doorbells are NOT requested if a VPE is not entering WFI as we expect to enter again imminently.”

版本 1 的补丁在代码风格上存在两个问题：引入了一个仅使用一次的布尔变量 `req_db`，以及将 `priority_mask` 和 `dbpm` 声明在过宽的作用域中。维护者 Marc Zyngier 对此提出改进建议，要求直接将条件表达式放入 `if` 判断，并将两个变量移入内部代码块，以增强可读性与作用域控制。

## 参与讨论人员
- **Sascha Bischoff** (Arm)
- **Marc Zyngier**（Linux arm64 维护者）

## 达成的结论
已达成共识。补丁作者 Sascha Bischoff 完全接受了 Marc Zyngier 的两项代码风格修改建议：
1. 移除多余的 `req_db` 变量，将 `vcpu_get_flag(vcpu, IN_WFI)` 直接作为 `if` 条件；
2. 将 `priority_mask` 和 `dbpm` 的声明移至内部代码块，缩小作用域。

作者在回复中明确表示 `Done`，双方对功能性逻辑没有异议，仅涉及编码规范。

## 下一步改进方向
- 根据 Marc 的反馈调整补丁代码，发布 v2 版本。
- 可能需要补充或加强针对门铃请求流程的测试用例，验证当 VPE 

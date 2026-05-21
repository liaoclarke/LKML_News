# KVM: arm64: pkvm: Remove struct cpu_sve_state

---

## 更新 - 2026-05-21 14:25 UTC

## 核心话题
该邮件是 Mark Rutland 提交的一个 KVM arm64 受保护模式（pkvm）清理补丁，核心目的是移除 `struct cpu_sve_state` 结构体，从而简化代码并提升健壮性，为后续引入不透明的 SVE 寄存器状态类型铺平道路。补丁指出，宿主机的 SVE 相关状态原本存储在 `cpu_sve_state` 中，但其中多个字段可以更自然地归入已有的 `kvm_cpu_context` 或直接使用 `user_fpsimd_state`，无需一个专门的容器结构。

具体来说，原本的 `cpu_sve_state` 包含了 `zcr_el1`、`fpsr`、`fpcr` 和 `sve_regs[]` 数组。Mark 发现 `kvm_cpu_context::sys_regs[]` 中已经有 `ZCR_EL1` 的槽位，因此可以直接将主机的 `ZCR_EL1` 值存储到该处，而不必在 `cpu_sve_state` 中单独维护。对于 `FPSR` 和 `FPCR`，虽然 `sys_regs` 中没有对应槽位，但这两个寄存器在保存/恢复 SVE 状态时通常放在 `user_fpsimd_state` 结构内；并且 `__sve_save_state` 和 `__sve_restore_state` 函数强依赖 `fpsr` 在 `user_fpsimd_state` 内的相对位置（假设 `fpcr` 紧跟其后）。当前 `cpu_sve_state` 中手动保持了这种顺序，但直接使用 `user_fpsimd_state` 会更加直接且不易出错。移除上述三个字段后，`cpu_sve_state` 只剩下 `sve_regs`，它可以用一个指向 `u8` 的指针来表示，这样既能正确表达 SVE 寄存器区，又能让编译器帮助捕捉非法的解引用/引用错误（优于 `void` 指针）。

补丁随后执行了这些改动：在 `kvm_host_data` 相关的上下文中用 `kvm_cpu_context` 内的 `ZCR_EL1` 替换；引入 `user_fpsimd_state` 变量来存放 `FPSR` 和 `FPCR`；将 SVE 寄存器数据表示为 `u8 *sve_regs` 指针。整个修改横跨 `kvm_host.h`、`kvm_pkvm.h`、`arm.c`、`hyp/switch.h`、`hyp-main.c` 等文件，最终删除了 `cpu_sve_state` 结构体定义及所有引用。

该清理的动机在于消除冗余的结构层次，减少托管 SVE 状态的分散程度，并为计划中的“不透明 SVE 状态类型”重构打好基础，避免现有结构成为累赘。

## 参与讨论人员
- Mark Rutland (Arm) — 补丁作者
- 抄送列表：
  - Catalin Marinas (Arm)
  - Fuad Tabba (Google)
  - James Morse (Arm)
  - Marc Zyngier (Kernel.org)
  - Mark Brown (Kernel.org)
  - Oliver Upton (Kernel.org)
  - Will Deacon (Arm)

（该线程目前仅有一封补丁邮件，无其他回复）

## 达成的结论
尚未达成明确共识。该邮件仅为补丁提交，是一系列 18 个补丁中的第 4 个，旨在征求审查意见。邮件中未出现后续讨论、反对意见或 Ack/Review 标签，因此可以认为补丁处于等待审核状态，讨论尚未展开。

## 下一步改进方向
1. 需要 ARM64 KVM 维护者（如 Marc Zyngier、Oliver Upton）及 SVE 相关领域专家（如 Mark Brown）对补丁进行技术审查，确认 ZCR_EL1 托管位置的正确性，以及直接使用 `user_fpsimd_state` 是否会影响现有保存/恢复逻辑的正确性。
2. 验证在受保护 KVM 环境中主机 SVE 状态切换的完整性，确保没有遗漏的保存/恢复路径（特别是 `__sve_save_state` 依赖的 `fpsr`/`fpcr` 顺序）。
3. 补丁是系列的一部分，可能需要依赖或照顾前后补丁的上下文，关注整个系列的一致性。
4. 如果有测试环境，应进行 pKVM + SVE 的回归测试，以保证无功能退化。

## 新增补丁
该线程中未出现新版本补丁，只有最初的 `[PATCH 04/18] KVM: arm64: pkvm: Remove struct cpu_sve_state`。

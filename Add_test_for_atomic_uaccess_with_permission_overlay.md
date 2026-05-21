# Add test for atomic uaccess with permission overlay

---

## 更新 - 2026-05-21 10:42 UTC

## 核心话题
本邮件线程围绕 ARM64 架构下权限覆盖（Permission Overlay Extension，POE）与原子用户空间访问（atomic uaccess）之间的交互问题展开。Kevin Brodsky 提交了一个包含两个补丁的系列（[PATCH 0/2]），旨在修复和加固 POE 机制在处理用户内存时的行为，并增加相应的回归测试。

**技术背景：**  
权限覆盖（POE）是 ARM64 的一种内存保护机制，允许在页表的基础上叠加额外的访问权限控制。PIR_EL1 寄存器用于配置哪些内存类型会被 EL1 特权级的权限覆盖检查所影响。在最新的内核实现中，Kevin 此前在引入基于 pkeys/POE 的页表保护系列时（参见链接 [1][2]），曾将 PIR_EL1 中所有内存类型都标记为应用权限覆盖，但这一改动后来被证实是错误的。

**核心问题：**  
根据 Sashiko 报告（引用 [3]），**用户内存类型绝对不能**在 PIR_EL1 中开启权限覆盖，否则会产生严重的安全和功能问题。具体来说，当内核使用特权加载/存储指令直接访问用户空间内存，且 PAN（Privileged Access Never）被禁用时，内存访问应该依据 **POR_EL0**（EL0 权限覆盖寄存器）进行检查，但如果 PIR_EL1 错误地为用户内存类型开启了覆盖，就会导致错误地使用 **POR_EL1** 进行权限检查，从而可能拒绝合法的访问或泄漏权限。

**补丁目标：**  
Kevin 明确指出，原子 futex uaccess 操作（在无 FEAT_LSUI 扩展的处理器上）会使用特权加载/存储指令来访问用户内存，因此上述错误配置会直接破坏这类原子操作。本系列的第一个补丁在 `arch/arm64/include/asm/pgtable-prot.h` 的 PIR_EL1 配置块上方添加了详细注释，警告不得为用户内存类型开启覆盖。第二个补丁则是一个全新的 kselftest，它确保在非默认 pkey 映射的内存上，原子 futex uaccess（如 futex 互斥锁操作）能正常工作，从而防止未来再次引入此类回归。邮件中强调：“To avoid any accident in the future, this series adds a comment above the PIR_EL1 configuration block, and a kselftest...”，直接说明了这一双重加固策略。

## 参与讨论人员
- **Kevin Brodsky** (Arm) —— 补丁作者
- **Catalin Marinas** (Arm) —— 抄送人
- **Joey Gouly** (Arm) —— 抄送人
- **Mark Brown** (kernel.org) —— 抄送人
- **Shuah Khan** (kernel.org) —— 抄送人
- **Will Deacon** (kernel.org) —— 抄送人
- （邮件中还提及了 Sashiko 作为错误的最初报告者，但未在抄送列表中直接出现）

## 达成的结论
由于提供的邮件仅包含整个系列的封面信（cover letter），且内容被截断（标注 `[...truncated...]`），**无法看到后续的讨论内容**。因此，基于现有信息，可作出如下观察：

- 这是一个新提交的补丁系列，尚未见到任何回复或审阅意见。
- 核心问题已经被清晰描述，即 PIR_EL1 错误配置会导致用户内存访问使用错误的权限覆盖寄存器，修复方案是添加注释和 new test。
- 截至目前，**尚未有明确的达成共识的记录**。需要等待相关维护者（如 Catalin Marinas、Will Deacon 等）的审阅，以决定是否接受这一补丁系列。

## 下一步改进方向
1. **补丁审阅**：aRM64 维护者（Catalin Marinas、Will Deacon）以及 POE/pkeys 相关开发者（Joey Gouly、Mark Brown）需要对两个补丁进行技术审阅，确认注释的准确性和测试用例的有效性。
2. **测试覆盖扩展**：当前的 kselftest 仅覆盖了原子 futex uaccess 场景，可能需要考虑在 PIR_EL1 相关回归测试中增加更多用户内存访问模式（如非原子 uaccess，以及不同 PAN 配置下的行为），但这是可选的后续增强。
3. **集成与合并**：本系列应被纳入 Kevin 的 pkeys/POE 主系列中，或作为预备修复提前合入，以保证主系列在最终启用 POE 时不会携带此已知错误。
4. **文档强化**：若审阅者认为注释不足以说明问题，可能需要讨论是否在架构相关文档中补充更详细的设计说明。

## 新增补丁
本次邮件直接提交了 **v1 系列（PATCH 0/2）**，包含以下两个新补丁：
- **补丁 1/2**：`arm64: mm: Add note about overlays in PIE_EL1` —— 在 PIR_EL1 配置块上方添加注释，说明为何不能为用户内存类型启用权限覆盖。
- **补丁 2/2**：`kselftest/arm64: Add test for atomic futex uaccess with POE` —— 新增 selftest `poe_futex.c`，测试在启用 POE 且使用非默认 pkey 映射时，原子 futex uaccess 能否正确执行。

该系列目前处于初始提交状态，邮件中未见到任何针对 v1 的修改版本。

# arm64: fpsimd: Move sve_flush_live() inline

---

## 更新 - 2026-05-21 14:25 UTC

## 核心话题
本邮件是 Mark Rutland 提交的一个补丁（系列中的第 16/18 个），旨在对 ARM64 架构下的 FPSIMD/SVE 状态管理进行重构与简化。补丁的核心内容是将原来独立用汇编编写的 `sve_flush_live()` 函数改为内联的 C 函数，并在此过程中剔除了两个事实上冗余的参数。

具体而言，原实现存在两个问题：
1. **`flush_ffr` 参数多余**：所有调用点均在非 streaming 模式下且始终传入 `true`，因此该标志无实际区分需要。补丁彻底移除该参数，并要求调用者必须在非 streaming 模式下执行。
2. **`vq_minus_1` 参数多余**：`sve_flush_live()` 内部完全可以直接通过 `RDVL` 指令（封装为 `sve_get_vl()` 辅助函数）读取当前活跃的向量长度（VL），无需由调用方传入。

基于以上分析，Mark 将汇编实现改写为 C 代码（内联形式），同时删除了 `fpsimdmacros.h` 中不再使用的相关汇编宏，以及 `entry-fpsimd.S` 中的独立汇编函数体。改动涉及 5 个文件，净增删 59 行汇编而新增 28 行 C 代码，整体上大幅减少了汇编维护负担，并且令控制流在 C 层面更清晰。

邮件中贴出的代码片段因截断未能展示完整的 C 实现，但开头 “st” 暗示了函数体可能使用了类似 `__sve_zero_p` 等内联宏来完成对 SVE 寄存器（除低 128 位外的部分）的清零操作。该补丁的动机正如原文所述：“It would be nice if we could move it inline such that control flow can be written more clearly in C, and to permit the removal of otherwise unused assembly macros.”（如果能把它内联化，以便在 C 中更清晰地编写控制流，并移除不再使用的汇编宏，那就太好了。）

## 参与讨论人员
- **Mark Rutland** <mark.rutland@arm.com>（补丁作者）
- **Catalin Marinas** <catalin.marinas@arm.com>
- **Fuad Tabba** <tabba@google.com>
- **James Morse** <james.morse@arm.com>
- **Marc Zyngier** <maz@kernel.org>
- **Mark Brown** <broonie@kernel.org>
- **Oliver Upton** <oupton@kernel.org>
- **Will Deacon** <will@kernel.org>

以上均列在邮件的 Cc 列表中，为相关维护者或对该代码有贡献的开发者。

## 达成的结论
当前邮件仅为补丁的单一投稿，未包含任何回复或讨论记录。因此**尚未达成任何共识或结论**。该补丁有待上述审核人员审阅、提出意见或测试确认后，才可能被接纳或要求修改。

## 下一步改进方向
- **代码审阅**：需要各维护者（尤其是 Will Deacon、Catalin Marinas 以及 FPSIMD/SVE 子系统负责人）审查该 C 实现是否正确完成了与汇编版完全相同的工作，特别是在清空高位部分的同时保留了每个向量的低 128 位。
- **调用上下文验证**：补丁声称所有调用点均在非 streaming 模式下且原来传递 `flush_ffr=true`，需确认现有及未来可能添加的调用路径不会违反该约束。可考虑在函数内增加 `WARN_ON_ONCE(system_supports_sme() && read_sysreg_s(SVCR) & SVCR_SM)` 之类的断言。
- **测试**：需在支持 SVE 的硬件或模型上进行回归测试，确认在保存/恢复 SVE 状态（如上下文切换、信号处理、KVM 虚拟化等场景）下不会引入向量寄存器高位或 FFR 的错误残留。
- **补丁系列整体推进**：该补丁是 18 个补丁系列中的一环，其有效性依赖前后补丁的上下文。审阅者需结合整个系列评估是否还有其他联动修改。

## 新增补丁
在本次邮件线程中并未出现该补丁的更新版本。当前帖子为**第一版（v1）**，补丁标题为 `[PATCH 16/18] arm64: fpsimd: Move sve_flush_live() inline`。后续若有修订，将可能以 v2 等形式单独发出。

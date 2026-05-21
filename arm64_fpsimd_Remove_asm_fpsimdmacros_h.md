# arm64: fpsimd: Remove <asm/fpsimdmacros.h>

---

## 更新 - 2026-05-21 14:25 UTC

## 核心话题
本补丁是Mark Rutland提交的“arm64: fpsimd: Refactor save/restore”系列（共18个补丁）中的最后一个，主旨是彻底删除`arch/arm64/include/asm/fpsimdmacros.h`头文件。该头文件自2012年起由Catalin Marinas引入，包含了用于ARM64汇编代码中保存与恢复FP/SIMD、SVE及SME状态的底层汇编宏，如Z寄存器和P寄存器范围检查宏（`_check_general_reg`、`_sve_check_zreg`、`_sve_check_preg`）、循环展开宏（`__for`）以及SME相关的选择寄存器检查宏（`_sme_check_wv`）等。这些宏过去被用于内核入口/出口路径、上下文切换以及KVM虚拟机切换时的FPSIMD状态保存与恢复操作。

然而，随着之前数个补丁将原本由汇编宏实现的保存恢复逻辑重写为C代码（例如将寄存器保存序列交由编译器生成，利用无条件批量加载/存储指令），这些宏已不再有任何用户。补丁明确指出“We no longer need any of the remaining macros”，因此将整个头文件连同其中的64行宏定义一并移除。这一改动简化了ARM64的FPSIMD维护体系，消除了历史遗留的复杂汇编依赖，提升了代码可读性和可维护性，符合现代内核倾向于将体系结构状态管理尽可能移至C代码的趋势。

## 参与讨论人员
- **Mark Rutland** (Arm) —— 补丁作者  
- **Catalin Marinas** (Arm) —— 抄送名单中，原`fpsimdmacros.h`作者  
- **Fuad Tabba** (Google)  
- **James Morse** (Arm)  
- **Marc Zyngier** (Arm / 内核社区)  
- **Mark Brown** (Arm)  
- **Oliver Upton** (Amazon)  
- **Will Deacon** (Arm)  
（以上均为补丁抄送对象，本邮件仅为补丁提交，尚未出现回应讨论，故严格来说该线程的参与者仅有作者本人。）

## 达成的结论
由于该邮件仅为补丁系列的最后一个补丁，它本身是单方面的提交行为，截至当前邮件内容，尚无任何维护者或其他开发者的回复、评审或讨论，因此尚未达成任何正式结论。预计该补丁将与其他17个补丁一同接受社区审查，若没有反对意见且能通过构建和回归测试，则可能被合入主线。

## 下一步改进方向
需要ARM64架构维护者（尤其是Catalin Marinas和Will Deacon）审核整个系列，确认移除`fpsimdmacros.h`后不会引起任何编译问题或功能缺失。具体包括：
- 验证所有曾包含该头文件的汇编文件（如`entry.S`、`fpsimd.S`等）已经剔除了相关引用；
- 确保内核在CONFIG_SVE、CONFIG_SME开启或关闭、KVM开启/关闭等多配置下的正确构建；
- 确认新的C级别保存/恢复代码逻辑正确，性能（特别是上下文切换延迟）无明显退化；
- 可能需要补充该头文件在Documentation/中的历史说明，或明确新用户应该使用何种替代接口。

## 新增补丁
本邮件仅提交了一个补丁，且是系列的第18/18个补丁，并未在回复中提供新的修订版本。

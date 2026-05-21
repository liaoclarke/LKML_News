# arm64: fpsimd: Remove sve_set_vq() and sme_set_vq()

---

## 更新 - 2026-05-21 14:25 UTC

## 核心话题
本补丁的主要目的是清理 ARM64 架构中 SVE（Scalable Vector Extension）和 SME（Scalable Matrix Extension）相关向量长度设置函数的实现。原有的 `sve_set_vq()` 和 `sme_set_vq()` 是两个用汇编语言实现的 out-of-line 函数，它们内部使用 `sve_load_vq` 和 `sme_load_vq` 宏来对系统寄存器进行 `ZCR_EL1` 或 `SMCR_EL1` 的写操作。开发者 Mark Rutland 指出这些汇编函数本质上只是对 `sysreg_clear_set*()` 系列辅助函数的开放编码（open-coded）实现，没有单独存在的必要。此外，这些函数的参数名称为 `vq_minus_1`，逻辑上要求调用者传入“向量四分之一长度（vq）减 1”后的值，这种编码方式与寄存器字段的实际格式直接对应，但在 C 语言接口中显得很不直观，容易造成混淆。

补丁直接移除这两个汇编函数及其声明，并在原先调用它们的位置改用 `sysreg_clear_set_s()` 宏。使用该宏时，所需的 `vq - 1` 编码可以直接在表达式中通过 `(vq - 1)` 显式体现，使得寄存器值的编码更为清晰。补丁作者在提交说明中强调“不应有任何功能变更”（There should be no functional change as a result of this patch.）。

值得注意的是，补丁刻意保留了 `sve_flush_live()` 函数的 `vq_minus_1` 参数，暂时没有一并修改，并明确指出会在后续补丁中解决该函数接口的类似问题，体现了逐步重构的思路。这一改动简化了 fpsimd 相关代码，减少了汇编文件中的自定义代码，有利于未来的维护和可读性。

## 参与讨论人员
- Mark Rutland (Arm) —— 补丁提交者。抄送列表中包含 Catalin Marinas, Fuad Tabba, James Morse, Marc Zyngier, Mark Brown, Oliver Upton, Will Deacon，但他们在本邮件线索中并未发表评论。

## 达成的结论
由于邮件线索中仅有补丁提交，没有后续的审查、评论或讨论，因此尚未就补丁的合入达成任何明确的共识。该补丁仍处于待审核状态。

## 下一步改进方向
1. 等待抄送列表中各维护者和相关开发者的审查与反馈（如 Ack / Reviewed-by 标签）。
2. 补丁中明确指出 `sve_flush_live()` 仍然使用不直观的 `vq_minus_1` 参数，将在后续补丁中予以处理，因此该系列后续补丁会继续进行接口统一和清理。
3. 需要确保所有使用 SVE/SME 的路径（如上下文切换、信号处理、ptrace 等）仍能正确工作，回归测试必不可少。

## 新增补丁
- **[PATCH 06/18]** （本邮件）: 移除 `sve_set_vq()` 和 `sme_set_vq()` 汇编函数，改用 `sysreg_clear_set_s()` 宏；删除了相关汇编代码、头文件声明和导出符号。

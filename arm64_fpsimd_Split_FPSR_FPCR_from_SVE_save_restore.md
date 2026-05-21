# arm64: fpsimd: Split FPSR/FPCR from SVE save/restore

---

## 更新 - 2026-05-21 14:25 UTC

## 核心话题
该邮件是 Mark Rutland 发布的 ARM64 FPSIMD/SVE 状态管理重构系列的第 11 个补丁，核心目标是将 **FPSR 和 FPCR 的保存/恢复逻辑从 SVE 向量寄存器上下文的 save/restore 函数中剥离出来**，形成独立的辅助函数。无论向量寄存器是以 FPSIMD 还是 SVE 格式存储，浮点状态寄存器 FPSR 与 FPCR 始终保存在 `user_fpsimd_state::{fpsr, fpcr}` 中，但现有的 SVE 保存/恢复函数仅接受一个指向 `user_fpsimd_state::fpsr` 的指针，并借此隐式地同时访问 `fpsr` 和 `fpcr`，这种依赖内存布局的约定非常脆弱。如作者所述：
> “... the functions which save/restore SVE context take a pointer to user_fpsimd_state::fpsr, and use this to access both user_fpsimd_state::fpsr and user_fpsimd_state::fpcr. This is unnecessarily

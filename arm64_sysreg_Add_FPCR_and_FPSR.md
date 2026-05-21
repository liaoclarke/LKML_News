# arm64: sysreg: Add FPCR and FPSR

---

## 更新 - 2026-05-21 14:25 UTC

## 核心话题
这封邮件是 ARM64 架构 sysreg 系列补丁的第 10/18 部分，主要内容是为 Linux 内核的 arm64 系统寄存器描述文件 `arch/arm64/tools/sysreg` 中添加 **FPCR**（Floating‑point Control Register）和 **FPSR**（Floating‑point Status Register）的完整定义。  
补丁的**技术动机**在于：内核中原本使用 `read_sysreg()` 与 `write_sysreg()` 宏来直接访问这些浮点控制/状态寄存器，但某些 LLVM 版本在汇编这些指令时，会要求启用 `"fp"` 架构扩展特性，否则直接拒绝汇编。若要在 `read_sysreg()` 等通用宏中处理这类特性依赖关系，会使宏定义变得异常复杂，不符合内核保持简洁的原则。因此补丁作者选择改用 `read_sysreg_s()` 和 `write_sysreg_s()`，这些宏需要精确的系统寄存器编码和字段定义才能生成正确的汇编，而不再依赖扩展特性自动推导。  
补丁引用 ARM ARM issue M.b 中 C5.2.8 和 C5.2.10 节的描述，将 FPCR 的编码为 `3 3 4 4 0`，FPSR 为 `3 3 4 4 1`，并详细列出了每一位字段。例如 FPCR 包含了 AHP、DN、FZ、舍入模式 RMode（RN/RP/RM/RZ）、Stride、FZ16、Len、以及 IDE、IXE、UFE、OFE、DZE、IOE 等异常使能位，还有 NEP、AH、FIZ 等控制位；FPSR 则定义了 N、Q、C、V、QC 等条件标志位以及 IDC、IXC、UFC、OFC、DZC、IOC 累积异常位。  
这一改动不仅是 sysreg 描述体系的扩充，也是为了后续在浮点上下文切换、信号处理等场景中，能够安全、明确地保存/恢复 FPCR 和 FPSR，而无需依赖可能不可用的 `"fp"` 扩展汇编支持。这是一项基础性基础设施完善，有助于提升内核在多样化工具链下的编译可靠性。

## 参与讨论人员
- Mark Rutland (Arm) — 补丁作者与提交者  
- Catalin Marinas (Arm)  
- Fuad Tabba (Google)  
- James Morse (Arm)  
- Marc Zyngier (Arm)  
- Mark Brown (Arm)  
- Oliver Upton (Arm)  
- Will Deacon (Arm)  
以上人员均出现在补丁的 Cc 列表，是相关子系统的维护者或关注者，但该邮件仅包含补丁提交，未见回复。

## 达成的结论
邮件线程中尚无任何回应，因此**尚未达成任何结论**。补丁目前处于提交待审状态，讨论未展开。

## 下一步改进方向
- 需要上述维护者对该定义进行**代码审查**，确认字段名称、位域划分与 ARM 架构手册完全一致，并确认在 LLVM 等受限工具链下的汇编行为符合预期。  
- 若审查通过，该补丁将被合入主线的 sysreg 定义文件，以供后续使用 `read_sysreg_s`/`write_sysreg_s` 的浮点状态管理代码引用。  
- 建议在实际启用 `read_sysreg_s` 访问 FPCR/FPSR 的后续补丁中，补充相应的**自测或编译测试**，确保在未启用 `"fp"` 特性的 LLVM 环境中也能正确生成代码。

## 新增补丁
当前邮件中仅包含系列中的 **PATCH 10/18**，并未在讨论中发布新版本，因此本线程内**无新增补丁**。

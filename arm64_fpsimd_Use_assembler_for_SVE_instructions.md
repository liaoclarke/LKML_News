# arm64: fpsimd: Use assembler for SVE instructions

---

## 更新 - 2026-05-21 14:25 UTC

## 核心话题
本封邮件是内核开发者 Mark Rutland 提交的一个补丁，属于一个多补丁系列（[PATCH 07/18]），针对 ARM64 架构下 SVE（Scalable Vector Extension）指令在内嵌汇编中的编码方式进行优化。该补丁的核心思想是：移除为 SVE 指令手动生成机器码（通过 `.inst` 伪指令）的老式做法，转而直接依赖当前工具链支持的汇编器（binutils 2.30+ 或 LLVM）来正常汇编 SVE 助记符指令。

补丁中明确指出，过去由于内核支持一些不能直接汇编 SVE 指令的旧版汇编器，因此在 `arch/arm64/include/asm/fpsimdmacros.h` 文件中，通过复杂的宏和 `.inst` 指令手动编码了 STR/LDR 等 SVE 向量指令。例如原来的 `_sve_str_v` 宏会先进行寄存器和立即数的范围检查，然后通过 `.inst 0xe5804000 | ...` 组合出二进制编码。而当前内核已经通过提交 `118c40b7b503 ("kbuild: require gcc-8 and binutils-2.30")` 将汇编器最低要求提升到能够原生支持 SVE 的版本，因此手动编码已无必要。

补丁的具体修改是将这些宏的内部实现改为使用 `.arch_extension sve` 开启 SVE 扩展，然后直接书写正常的汇编指令 `str z\nz, [X\nxbase, #\offset, MUL VL]`，并保留原始的宏名称（如 `_sve_str_v`），这样外部调用者不受影响。作者明确表示，暂时保留这些宏，后续补丁会进一步清理。这种改动不产生功能性变化，纯粹是清理历史遗留代码，提高了代码可读性和可维护性，也降低了未来引入错误的概率。

邮件中 Mark Rutland 指出，由于所有受支持的汇编器（GNU binutils 和 LLVM）现在都已经支持 SVE，这种依赖汇编器原生编码的方式可以安全地替代原有的手动编码，并且避免了手工维护指令编码的负担。这体现了内核代码在工具链升级后同步清理旧有兼容性代码的常规维护思路。

## 参与讨论人员
*   Mark Rutland (Arm) —— 补丁作者
*   Catalin Marinas (Arm) —— 被抄送，ARM64 维护者
*   Fuad Tabba (Google) —— 被抄送
*   James Morse (Arm) —— 被抄送
*   Marc Zyngier (kernel.org) —— 被抄送
*   Mark Brown (kernel.org) —— 被抄送
*   Oliver Upton (kernel.org) —— 被抄送
*   Will Deacon (Arm) —— 被抄送

本邮件为补丁提交邮件，截至当前提供的邮件内容，尚未出现任何回复或讨论。

## 达成的结论
在此邮件线程中，由于仅有补丁提交而无后续回复，尚未形成任何明确的社区共识或结论。补丁作为系列的一部分发布，意图是清理不再需要的手工 SVE 指令编码，逻辑上符合工具链最低版本提升后的合理清理方向。目前的状态是等待相关维护者（如 Catalin Marinas、Will Deacon）以及其他被抄送者的审查反馈。如果后续没有反对意见，该补丁可能被合并，但目前无确认的结论。

## 下一步改进方向
1.  **审查与测试：** 需要 ARM64 维护者或 SVE 相关开发者对该补丁进行审查，确认移除手动编码后，新的汇编器编码方式在所有支持的 binutils 和 LLVM 版本下行为完全一致，且无性能回归。
2.  **后续清理：** Mark Rutland 在邮件中明确说明 “The various _sve_<insn> macros are kept for now, and will be cleaned up in subsequent patches.” 因此，本补丁只是过渡步骤，后续需要提交新补丁来彻底移除这些临时保留的 `_sve_` 宏，并将剩余的调用点直接转换为标准汇编指令。
3.  **完整系列审查：** 由于是 18 个补丁系列中的第 7 个，需要结合整个系列的目标来理解此改动的上下文，确保清理步骤的顺序合理，不影响其他补丁的功能。
4.  **文档更新：** 如果清理后的代码行为有任何值得注意的变化（尽管声称无功能改变），可能需要更新相关的注释或文档。

## 新增补丁
本线程中仅包含原始补丁提交 `[PATCH 07/18] arm64: fpsimd: Use assembler for SVE instructions`（可视为版本 1）。尚未出现针对该补丁的新版本（如 v2）或修正补丁。

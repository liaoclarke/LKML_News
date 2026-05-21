# arm64: fpsimd: Move SME save/restore inline

---

## 更新 - 2026-05-21 14:25 UTC

## 核心话题
该补丁是 Mark Rutland 提交的系列补丁中的第 17 个，目标是将 ARM64 SME（Streaming Matrix Extension）的寄存器保存/恢复操作从**外联汇编**（out-of-line assembly）迁移到**内联汇编**（inline assembly）中实现。当前相关逻辑位于 `arch/arm64/kernel/entry-fpsimd.S` 中，用汇编宏完成 ZA 寄存器等内容的存取，但这种方式带来了一系列问题。补丁描述中明确列出了四大痛点：

1. **KVM 复用困难且易导致维护负担**：KVM 的 hyp 代码需要复制部分保存/恢复逻辑，虽然用汇编宏可以共享，但“非常容易产生不必要的分歧并成为维护负担”。
2. **汇编宏接口晦涩**：“sme_save_za 0, x2, 12 这类用法用数字索引指定寄存器，简直让人困惑”。
3. **C 代码的控制流和地址生成更清晰**：“地址生成和控制流在 C 中远比汇编清晰”。
4. **无法插桩检测内存安全问题**：汇编序列不能被 KASAN 等工具检测，“导致更难发现内存安全问题”。

解决方案是将 SME 寄存器保存/恢复序列改写为内联汇编，放置于 `arch/arm64/include/asm/fpsimd.h` 中。内联汇编虽不会被 GCC/LLVM 自动插桩，但补丁以与其他汇编例程相同的方式添加了显式插桩，且该插桩在 Kbuild 处理 nVHE hyp 代码时会被隐式禁用，从而不影响 KVM 的隔离环境。  
在代码变更上，补丁删除了 `arch/arm64/kernel/entry-fpsimd.S` 的 99 行代码及 `arch/arm64/include/asm/fpsimdmacros.h` 中的相关宏定义，并在 `fpsimd.h` 中新增了约 100 行内联汇编封装。这显著减少了独立汇编文件的使用，使核心逻辑回归 C 文件，利于维护、共享和调试。

## 参与讨论人员
* **Mark Rutland** (Arm) — 补丁作者
* **Catalin Marinas** (Arm)
* **Fuad Tabba** (Google)
* **James Morse** (Arm)
* **Marc Zyngier** (Kernel.org) — 通常代表 Arm
* **Mark Brown** (Kernel.org) — 通常代表 Arm
* **Oliver Upton** (Kernel.org) — 通常代表 Google
* **Will Deacon** (Kernel.org) — 通常代表 Arm

以上为补丁 Cc 列表中的维护者与相关开发者，但该线程中仅出现原作者的补丁提交，尚无其他人的回应。

## 达成的结论
该邮件仅为补丁提交，尚未出现任何回复或讨论。因此线程内**未达成任何共识**，所有技术问题均处于待评审状态，等待上述维护者及社区的意见。

## 下一步改进方向
1. **社区评审**：需要 Arm64 维护者（Catalin、Will 等）、KVM 维护者（Marc、Oliver）、相关 SME/SVE 开发者（Mark Brown、Fuad Tabba）审查补丁，确认内联汇编的正确性、性能影响以及与 KVM hyp 代码的兼容性。
2. **测试验证**：需要在硬件或模拟器上测试 SME 状态保存/恢复的完整性，尤其关注 CONFIG_KASAN 等内存检测工具开启时的插桩是否正确工作，以及 nVHE hyp 代码中插桩被正确屏蔽。
3. **后续整合**：该补丁是 18 个补丁系列的一部分，可能依赖前序补丁，需确保整个系列被一起评审和应用后的稳定性。
4. **可能的修改**：根据评审意见调整内联汇编的约束、内存 clobber 说明，或者进一步合并到 KVM 共享路径中。

## 新增补丁
* **[PATCH 17/18] arm64: fpsimd: Move SME save/restore inline** （初版，即本邮件所附补丁）  
  主要改动：删除 `arch/arm64/kernel/entry-fpsimd.S` 及相关宏，在 `fpsimd.h` 中使用内联汇编实现 SME 状态保存/恢复，并增加显式 KASAN 插桩。此为该补丁在本线程中的唯一版本，尚未有后续修订。

# arm64: fpsimd: Move sve_get_vl() and sme_get_vl() inline

---

## 更新 - 2026-05-21 14:25 UTC

## 核心话题
该补丁来自 ARM64 架构维护者 Mark Rutland 提交的一个系列补丁（[PATCH 09/18]），目标是将原本在 `arch/arm64/kernel/entry-fpsimd.S` 中以汇编函数形式实现的 `sve_get_vl()` 和 `sme_get_vl()` 改为在头文件中以内联汇编方式实现。这两个函数分别封装了 RDVL 和 RDSVL 指令，用于获取当前硬件支持的 SVE 和 SME 向量长度（Vector Length），属于简单的单条指令查询操作，没有必要保留独立的外联函数调用开销。

Mark Rutland 在提交说明中指出：“The sve_get_vl() and sme_get_vl() functions are wrappers for the RDVL and RDSVL instructions respectively. There's no need for those to be out-of-line.”（这两个函数只是 RDVL 和 RDSVL 指令的包装，无需保留外联形式）。因此补丁将它们改为 `static inline` 函数，使用内联汇编直接嵌入指令，避免了函数调用带来的栈帧和跳转开销，并有助于编译器更好地优化代码。

与此同时，补丁还清理了相关的汇编宏：由于 `_sve_rdvl` 宏在本次转变后已无任何使用者，被直接移除；而 `_sme_rdsvl` 宏仍被其他地方引用，因此先保留不动。为了支持内联汇编中正确使用架构扩展，补丁在 `arch/arm64/include/asm/fpsimd.h` 头部新增了两个宏定义：
```c
#define __SVE_PREAMBLE     ".arch_extension sve\n"
#define __SME_PREAMBLE     ".arch_extension sme\n"
```
这使得编译器在遇到 SVE/SME 内联汇编时能够自动启用对应扩展，保证汇编指令通过编译。

补丁展示了具体的代码转换，例如新增的 `sve_get_vl()` 实现：
```c
static inline unsigned int sve_get_vl(void)
{
    unsigned int vl;
    asm volatile(
    __SVE_PREAMBLE
    "   rdvl %x[vl], #1\n"
    : [vl] "=r" (vl)
    );
    return vl;
}
```
这清晰地用约束将结果写入 C 变量并返回，实现了等效功能。

该修改属于 fpsimd 子系统优化的一部分，目的是减少微不足道的外联函数、统一代码风格并提高内核效率，尤其是对像向量长度查询这样频繁但不耗时的路径有明显好处。

## 参与讨论人员
- Mark Rutland（Arm），补丁作者
- 邮件抄送的潜在关注者（未在讨论中发言）：
  - Catalin Marinas（Arm）
  - Fuad Tabba（Google）
  - James Morse（Arm）
  - Marc Zyngier（Kernel.org / 曾任 Arm）
  - Mark Brown（Kernel.org）
  - Oliver Upton（Kernel.org）
  - Will Deacon（Google / 曾任 Arm）

由于该邮件仅是补丁提交，截至被封存的内容中尚未出现其他人的回复或讨论，实际参与讨论的仅 Mark Rutland 一人。

## 达成的结论
尚未形成任何共识或结论。这是一封孤立的补丁提交邮件，没有后续的评审意见、讨论或 Ack/Review 标签。整个补丁系列（18 个补丁）还需要通过邮件列表的审查流程，才能得出是否被接纳的结论。

## 下一步改进方向
1. **审查与反馈**：需要其他维护者（特别是 Will Deacon、Catalin Marinas 等 Arm64 维护者）以及感兴趣的开发者对补丁进行审查，检查内联汇编是否正确，是否存在性能或正确性问题。
2. **系列整体协调**：由于这是 09/18 的补丁，需考虑整个系列的内聚性。如果其他补丁修改了对这两个函数的调用约定或上下文，这个补丁可能需要相应调整。
3. **测试**：内联版本需要在支持 SVE 和 SME 的硬件或模拟器上进行测试，确保 RDVL/RDSVL 在功能上与外联版本完全一致，且不影响向量长度相关逻辑。
4. **宏清理**：如果后续有其他代码重构，`_sme_rdsvl` 也被消除使用后，可进一步清理掉该宏。
5. **合并准备**：待补丁获得充分的 Reviewed-by/Acked-by 后，由 ARM64 维护者将其合入相应分支。

## 新增补丁
该线程仅包含原始补丁提交，没有发布新的修订版本。该补丁属于系列中的第 9 个补丁，当前可视为第一版（v1），具体补丁标题为：
`[PATCH 09/18] arm64: fpsimd: Move sve_get_vl() and sme_get_vl() inline`
其中未出现 v2 等后续版本标记。

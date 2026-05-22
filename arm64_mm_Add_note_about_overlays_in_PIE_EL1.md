# arm64: mm: Add note about overlays in PIE_EL1

---

## 更新 - 2026-05-21 10:42 UTC

## 核心话题
本邮件是 Kevin Brodsky 提交的一个小型注释补丁，属于 `[PATCH 1/2]` 系列的一部分，目标是在 ARM64 架构的 `pgtable-prot.h` 头文件中为 `PIE_EL1` 宏增加代码注释，解释**为何不为常规用户页表类型（如 `_PAGE_SHARED`）应用权限覆盖（overlays）**。整个讨论目前仅包含这一封提交邮件，没有后续回复，因此核心话题集中在这项注释背后的技术动机。

从补丁内容和注释原文可以看到，技术背景围绕 ARM64 的两项内存权限扩展：**POE（Permission Overlay Extension）** 和 **PIE（Permission Indirection Extension）**。`PIE_EL1` 宏利用 `PIRx_ELx` 寄存器定义了 EL1 下不同页表权限索引（`pte_pi_index`）所对应的间接权限，其中用户页类型如 `_PAGE_SHARED` 没有被赋予任何 overlay（即使用默认权限）。注释的关键解释在于：

> “如果 POE 在 EL1 使能，并且缺少 FEAT_LSUI，则会对用户内存的 futex 原子操作产生破坏；特权原子加载/存储指令会被错误地根据 POR_EL1 进行检查。”

这意味着，如果为常规用户页类型在 EL1 的 `PIR_EL1` 中应用了 overlay，当 EL1 使用特权原子指令（例如用于内核中的 futex 操作）访问用户空间地址时，且硬件未提供 **FEAT_LSUI**（Load/Store Unprivileged Instructions 的改进，允许原子指令绕过权限覆盖检查），那么硬件会根据 `POR_EL1`（Permission Overlay Register for EL1）而非针对用户空间的权限设置来检查访问合法性，造成原本合法的原子操作失败，破坏 futex 等关键内核功能。因此，补丁特意增加注释以警示未来开发者不要误以为此处缺少 overlay 是一个疏漏，避免引入严重回归。补丁本身是纯文档性的，没有逻辑变更。

## 参与讨论人员
- **Kevin Brodsky** (Arm)

## 达成的结论
该邮件为独立的补丁提交，尚无其他参与者回复或审查，因此**未形成正式结论**。作者通过补丁表达了明确的技术观点：PIE_EL1 中不对用户页类型添加 overlay 是有意为之，基于对 POE 与 FEAT_LSUI 交互的风险考量。这更像是一个待合入的解释性清理，等待社区评审确认。

## 下一步改进方向
- 等待 ARM64 维护者或其他开发者审查该注释的准确性，并确认是否需要更详细的解释或指向架构手册的相关章节。
- 该补丁作为 `[PATCH 1/2]` 的一部分，需与第二个补丁（可能涉及其他相关代码或进一步注释）一同被评审，确保整个系列的表达一致且完整。
- 如果评审过程中有人对 POE / PIE 的交互有更深入的问题，可能需要扩展注释内容或补充文档。

## 新增补丁
- `[PATCH 1/2] arm64: mm: Add note about overlays in PIE_EL1`（本邮件）：在 `arch/arm64/include/asm/pgtable-prot.h` 中为 `PIE_E1` 宏增加 7 行注释，说明常规用户页类型不添加 overlay 的原因，避免未来因误解而错误修改。

---

## 更新 - 2026-05-22 10:20 UTC

## 核心话题
本邮件讨论的是针对 arm64 内存管理中的 PIE_EL1 权限索引覆盖（overlay）机制添加代码注释的补丁。补丁作者 Kevin Brodsky 注意到，PIE_E1 宏仅为某些特定的用户页类型（如 _PAGE_GCS 等）设置了覆盖，而常规用户页类型（如 _PAGE_SHARED）则未被覆盖。其技术原因并非显而易见，若未来有人在不理解背景的情况下随意添加覆盖，可能引入严重问题。

补丁说明明确指出：“如果启用了 EL1 级别的 POE（Permission Overlay Extension），并且在缺乏 FEAT_LSUI 特性的情况下，对用户内存使用非默认 POIndex 的 futex 原子操作将会被破坏；特权原子加载/存储指令将错误地按照 POR_EL1 进行检查。” 因此，注释强调“Regular user page types such as _PAGE_SHARED must not have overlays applied in PIE_EL1”，以避免此类意外。

该注释直接添加在 PIE_E1 宏定义之前，为后续开发者明确约束条件。回复者 Yeoreum Yun 审阅后认为“LGTM”，并给出 Reviewed-by 标签，表明该注释清晰、准确地记录了现有实现中的隐含约束，有利于代码可维护性。

## 参与讨论人员
- Yeoreum Yun (Arm)
- Kevin Brodsky (Arm)

## 达成的结论
Yeoreum Yun 完全认可该补丁，并给出了 Reviewed-by，因此该补丁在讨论中已获得审查通过，没有残留的分歧或反对意见。

## 下一步改进方向
该补丁内容仅增加注释，无需行为变更或进一步讨论，可直接进入合入流程（例如由维护者拣选）。如果当前系列还有其他补丁待审，需同步推进。

## 新增补丁
本邮件是对原补丁（PATCH 1/2）的审查回复，并未在对话中发布新的补丁版本。原补丁信息如下：
- **补丁标题**：arm64: mm: Add note about overlays in PIE_EL1
- **版本**：v1（首次提交，与同一系列另一补丁 PATCH 2/2 配对）
- **变更摘要**：在 arch/arm64/include/asm/pgtable-prot.h 中 PIE_E1 宏上方增加 7 行注释，说明为何不对常规用户页类型应用权限覆盖，以防止在缺少 FEAT_LSUI 且启用 EL1 POE 时破坏 futex 原子操作。

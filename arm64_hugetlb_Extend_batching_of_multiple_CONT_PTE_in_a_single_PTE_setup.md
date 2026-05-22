# arm64/hugetlb: Extend batching of multiple CONT_PTE in a single PTE setup

---

## 更新 - 2026-05-22 13:31 UTC

## 核心话题
该邮件是由 Wen Jiang 发出的 v3 版本补丁系列的第一部分（[PATCH v3 1/6]），实际作者为 Barry Song (Xiaomi)。补丁旨在扩展 arm64 架构下大页的批量映射能力：对于大小对齐到 CONT_PTE_SIZE（64KB，当 4KB 页时）且小于 PMD_SIZE（2MB）的大页尺寸（例如 128KB、256KB、512KB、1MB 等），原先的代码只对标准的 PMD_SIZE 或 CONT_PTE_SIZE 进行处理，而这些中间尺寸会触发 WARN_ON(!__hugetlb_valid_size(size)) 警告并被忽略。补丁修改了两个核心函数：

1. 在 `num_contig_ptes()` 函数中（计算连续的 PTE 数量），增加了 `default` 分支的处理：如果 `size > 0 && size < PMD_SIZE && IS_ALIGNED(size, CONT_PTE_SIZE)`，则将 `contig_ptes` 设置为 `size >> PAGE_SHIFT`（即页数），并设置 `*pgsize = PAGE_SIZE`。这样对于 128KB（32 个 4KB 页，对齐到 64KB 的倍数），会返回连续 PTE 数为 32，并以单个页面大小为基础进行后续处理，避免了因无法识别尺寸而出现的警告和错误。

2. 在 `arch_make_huge_pte()` 函数中（标记大页 PTE 的连续位），同样在 `default` 分支添加了类似检测：若 `pagesize` 符合对齐且小于 PMD_SIZE 的条件，则直接返回 `pte_mkcont(entry)`，即设置 PTE 的连续位，使得多个连续的 PTE 被硬件视为一个大页 TLB 条目，从而提升 TLB 覆盖范围和性能。

该补丁的技术动机是：ARM64 架构支持通过设置连续位（Contiguous bit）将多个连续的 PTE 合并为一个 TLB 条目，原本仅用于 64KB 对齐（CONT_PTE_SIZE）的标准大页。但某些场景下可能使用更大的对齐尺寸（例如 128KB、256KB 等），这些尺寸并未被现有代码支持。补丁通过简单的条件判断，将这些对齐到 CONT_PTE_SIZE 的中间尺寸统一处理，使内核能够在设置大页映射时一次性批量设置多个 CONT_PTE，而非逐项设置，从而提升地址空间布局和映射效率。邮件中仅包含补丁本身，没有讨论内容，因此没有技术争论。

## 参与讨论人员
- **Wen Jiang**（邮件发送者，邮箱 jiangwenxiaomi@gmail.com）
- **Barry Song (Xiaomi)**（补丁原作者，邮箱 baohua@kernel.org）
- **Xueyuan Chen**（测试者，邮箱 xueyuan.chen21@gmail.com）

## 达成的结论
由于该邮件仅包含补丁提交，没有出现任何回复或讨论，因此 **未达成任何结论**，补丁处于待审查状态。

## 下一步改进方向
- 需要 ARM64 子系统的维护者及社区开发者对该补丁进行审查，评估其正确性和对现有内存管理代码的影响。
- 可能需要测试更多与对齐相关的大页尺寸，确保不会引入边界条件错误（如 `size == 0` 的情况已在补丁中通过 `size > 0` 排除）。
- 考虑补丁是否需要对 `__hugetlb_valid_size()` 函数同步调整，以消除原有的 WARN_ON 警告，但目前补丁通过直接处理合法尺寸绕过了警告，可能后续还需规范该处逻辑。
- 补丁作为系列的第一部分，其后的 5 个补丁尚未在此邮件中展示，需完整系列一同审查，以确保整体功能的连贯性。

## 新增补丁
该邮件中提供的是 **v3** 版本补丁（[PATCH v3 1/6]），相对于之前 v1/v2 版本的具体变更未在邮件中说明，但根据内容可见该补丁已进入第三轮迭代，表明可能在前序版本中收到了修改建议。当前补丁在 `num_contig_ptes()` 和 `arch_make_huge_pte()` 两个函数中增加了对对齐到 CONT_PTE_SIZE 且小于 PMD_SIZE 的中间尺寸的支持。

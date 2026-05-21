# arm64: mm: call pagetable dtor when freeing hot-removed page tables

---

## 更新 - 2026-05-21 13:27 UTC

## 核心话题
该补丁由 Alistair Popple 提交，旨在修复 ARM64 架构在内存热移除时，因释放页表页而未调用相应的析构函数（pagetable_dtor）所引发的问题。自提交 5e8eb9aeeda3 ("arm64: mm: always call PTE/PMD ctor in __create_pgd_mapping()") 以来，ARM64 在分配页表页时总是调用 `pagetable_{pte,pmd,pud,p4d}_ctor()`，这些构造函数会将 `page_type` 设置为 `PGTY_table`，增加 `NR_PAGETABLE` 统计计数，并在特定配置下（`ALLOC_SPLIT_PTLOCKS`）为页表分配 PTL（page table lock）。然而，在热移除流程中通过 `free_empty_tables()` 释放这些页表页时，从未调用与之对应的 `pagetable_dtor()` 来撤销构造函数所执行的操作。

这导致了几个具体问题：在 v6.17 之前、未包含提交 2dfcd1608f3a9 ("mm/page_alloc: let page freeing clear any set page type") 的内核上，若启用了 `DEBUG_VM`，当这些页被释放并经过页分配器校验时，会触发 `Bad page state` 警告，因为 `page->page_type` 仍为 f2(table)，而该字段与 `page->_mapcount` 共享联合体，系统错误地报告“nonzero mapcount”。提交中给出了完整的调用栈，清晰地展示了该问题产生于 `offline_and_remove_memory` → `arch_remove_memory` → `__remove_pgd_mapping` → `free_empty_tables` → `free_hotplug_pgtable_page` 的路径上。即使后续提交 2dfcd1608f3a9 在释放时强制清除了 page type，不再触发 VM_BUG，但仍然会残留 `NR_PAGETABLE` 统计不准确的问题，并且在启用 `ALLOC_SPLIT_PTLOCKS` 时，分配到页表的 PTL 不会被释放，从而造成内存泄漏。补丁通过在 `free_hotplug_pgtable_page()` 中，于 `free_the_page()` 之前添加 `pagetable_dtor(page)` 调用，来彻底解决这些残留副作用。补丁明确标记了 `Fixes: 5e8eb9aeeda3 ("arm64: mm: always call PTE/PMD ctor in __create_pgd_mapping()")`。

## 参与讨论人员
- Alistair Popple (NVIDIA)

## 达成的结论
该邮件仅包含初始补丁提交，线程中未出现任何回复或讨论，因此尚未达成任何社区共识或技术结论。补丁所描述的问题和解决方案需要经过维护者或相关开发者的审查。

## 下一步改进方向
1. 需要 ARM64 内存管理维护者（如 Catalin Marinas、Will Deacon 等）或其他核心开发者审阅该补丁，确认在 `free_hotplug_pgtable_page()` 中添加 `pagetable_dtor()` 的时机和正确性。
2. 讨论是否需要在补丁描述中进一步阐明：即便内核已包含 2dfcd1608f3a9（清除了 page type），该修复对于纠正 `NR_PAGETABLE` 统计和避免潜在的 PTL 泄漏仍然必要。
3. 验证补丁是否需要在长期支持（LTS）或较早的稳定内核上进行回溯（backport），尤其是对于同时启用了内存热插拔和 DEBUG_VM 的系统。
4. 执行更多测试，特别是针对内存热移除路径下不同级页表（PTE、PMD、PUD、P4D）的释放场景，确保析构调用不会引入新的问题。
5. 检查 ARM64 下是否还有其他释放页表且遗漏 `pagetable_dtor()` 的路径，以保证完整性。

## 新增补丁
- **[PATCH] arm64: mm: call pagetable dtor when freeing hot-removed page tables** (版本 v1)：提交者 Alistair Popple，在 `arch/arm64/mm/mmu.c` 的 `free_hotplug_pgtable_page()` 函数中增加了 `pagetable_dtor(page);` 一行，以确保在页表页最终释放前撤销构造函数的效果。

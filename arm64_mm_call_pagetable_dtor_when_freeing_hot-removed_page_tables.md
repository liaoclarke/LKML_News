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

---

## 更新 - 2026-05-22 09:50 UTC

## 核心话题
本次讨论围绕一个 arm64 架构下内存热拔出（hot-remove）过程中页表释放的缺陷展开。问题的根源在于提交 `5e8eb9aeeda3`（"arm64: mm: always call PTE/PMD ctor in __create_pgd_mapping()"），该提交使得 arm64 在创建页表映射时统一调用了页表构造函数 `pagetable_{pte,pmd,pud,p4d}_ctor()`。这些构造函数会将 `page_type` 设置为 `PGTY_table`，增加内核统计 `NR_PAGETABLE`，并且在配置了 `ALLOC_SPLIT_PTLOCKS` 的情况下还会分配页表锁（PTL）。然而，对应的页表释放路径并未调用析构函数 `pagetable_dtor()`，导致这部分资源未能正确清理。

当启用 `DEBUG_VM` 且在未包含补丁 `2dfcd1608f3a9`（该补丁会在释放页面时主动清除 `page_type`）的 v6.17 之前内核上，该问题会以“Bad page state”警告的形式暴露出来。具体原因是 `page->page_type` 与 `page->_mapcount` 共用存储空间，而未经析构的页面在释放时残留的 `page_type`（如 `f2(table)`）会被解释为非零的 `mapcount`，从而触发 `bad_page()` 校验失败。Alistair Popple 在邮件中给出的实际调用栈清晰地展示了这一过程：从 `offline_and_remove_memory` -> `free_empty_tables` -> `free_hotplug_page_range` -> `free_pages` -> `__free_pages` -> `__free_frozen_pages` -> `bad_page`。除此之外，该缺陷还可能导致页表锁内存泄漏以及 `NR_PAGETABLE` 统计值偏高。

Alistair 提出的修复方法是在热拔出释放页表页的函数 `free_hotplug_pgtable_page()` 中，于最终释放页面之前先调用 `pagetable_dtor()`，以此逆转构造函数造成的所有影响，保证页表生命周期管理的对称性。Andrew Morton 在审核时指出，该问题影响 Linux 6.16 及后续版本，因此需要补充 `cc: stable` 标记以便向后移植。Alistair 立即认同了这一判断，并对 Andrew 主动补上 stable 标签表示感谢。整个讨论虽然简短，但技术逻辑清晰，确认了补丁的必要性和稳定性需求。

## 参与讨论人员
- Alistair Popple <apopple@nvidia.com> (NVIDIA)
- Andrew Morton <akpm@linux-foundation.org> (Linux 基金会)

## 达成的结论
已达成完全共识。双方均认为该修复正确且必要，并且必须合入 stable 树。Andrew Morton 已自行在补丁中补充了 `cc: stable` 标记，Alistair Popple 对此表示认可并感谢。讨论中未出现任何异议或分歧。

## 下一步改进方向
该补丁需要被正式合入主线。由于 Andrew Morton（-mm 树维护者）已接手处理，它预计会先进入 -mm 树的 mm-hotfixes 分支，并最终在下一个合并窗口或作为修复直接合入 Linus 主线。同时，由于标明了 stable，修复将被反向移植到 v6.16 及之后受影响的稳定内核版本。目前无需进一步的代码修改或额外讨论，等待合入

---

## 更新 - 2026-05-22 08:15 UTC

## 核心话题
本邮件讨论围绕一个ARM64架构的内存热移除（memory hot-remove）缺陷修复补丁展开。核心问题是：自上游提交 `5e8eb9aeeda3`（"arm64: mm: always call PTE/PMD ctor in __create_pgd_mapping()"）合入后，ARM64 在创建页表时总是调用 `pagetable_{pte,pmd,pud,p4d}_ctor()`，该构造函数会设置 `page_type` 为 `PGTY_table`、增加 `NR_PAGETABLE` 统计计数，并且在启用了 `ALLOC_SPLIT_PTLOCKS` 的情况下还可能分配页表锁（PTL）。然而，在内存热移除流程中释放页表时，对应的 `pagetable_dtor()` 析构函数从未被调用，导致页的 `page_type` 未被清除、`NR_PAGETABLE` 统计错误，以及潜在的 PTL 内存泄漏。

这个缺陷在启用 `DEBUG_VM` 且运行早于 v6.17（没有 commit `2dfcd1608f3a9` "mm/page_alloc: let page freeing clear any set page type"）的内核上会直接触发 VM BUG 警告。警告发生在 `free_pages()` -> `__free_pages()` -> `__free_frozen_pages()` -> `bad_page()` 路径中，原因是 page 的 `page_type` 共享了 `_mapcount` 字段，释放时 mapcount 非零被视为异常，从而报告 "nonzero mapcount" 并 dump 页信息（如 page_type: f2(table)）。调用栈明确指向热移除流程：`free_empty_tables()` -> `free_hotplug_page_range()` -> `free_pages()`。

补丁作者 Alistair Popple 的修复非常直接：在 `free_hotplug_pgtable_page()` 中调用 `pagetable_dtor()` 之后再释放页面，从而反转构造函数的影响。Andrew Morton 在回复中明确指出该问题影响 6.16+ 内核，并建议补丁需要标注 `cc: stable` 以向后移植到稳定版。Catalin Marinas 作为 ARM64 维护者参与了审核。

## 参与讨论人员
- **Alistair Popple** (NVIDIA) — 补丁作者，发现并修复该问题。
- **Andrew Morton** — 资深内核维护者，提出应标记 `cc:stable`。
- **Catalin Marinas** (Arm) — ARM64 架构维护者，参与审核与回复。

## 达成的结论
讨论中已达成明确共识：该缺陷确实存在，修复方案 (`pagetable_dtor()`) 正确且必要。Andrew Morton 明确指出需要标记 `cc:stable`，以覆盖受影响的稳定版内核（6.16+）。Catalin Marinas 的回复（邮件内容被截断，但作为维护者参与）可合理推断为认可该修复。因此，该补丁将被合入主线并附带 `Fixes: 5e8eb9aeeda3` 标签以及 `Cc: stable` 注释。

## 下一步改进方向
- 补丁需要由 ARM64 维护者（Catalin Marinas）排队合入 `arm64` 树，或通过 `mm` 树合入上游。根据现有讨论，预计很快会被采纳。
- 必须确保补丁包含正确的 `Fixes` 标签和 `Cc: stable` 声明，以便稳定版维护者能自动或手动将其移植到 v6.16 至 v6.17-rc 之间的版本。
- 考虑到补丁修复的是页释放路径，建议关注是否需要在其他可能有类似构造/析构不匹配的架构或流程中进行类似修复，但目前本补丁仅针对 ARM64 热移除路径。

## 新增补丁
本次邮件线程中**没有出现新的补丁版本**，仅有一个初始补丁（v1）被讨论和评审。作者没有基于反馈再发 v2，因为评审者已直接给出了赞同意见和 `cc:stable` 建议。因此，最终合入的补丁内容应与此处展示的初始版本一致，仅需加入 `Cc: stable` 标记。

---

## 更新 - 2026-05-22 10:36 UTC

## 核心话题
本邮件线程围绕 ARM64 架构热移除内存时页表释放过程缺少 `pagetable_dtor()` 调用的问题展开。问题的根源在于 commit 5e8eb9aeeda3（"arm64: mm: always call PTE/PMD ctor in __create_pgd_mapping()"），该提交使 ARM64 在创建各级页表（PTE、PMD、PUD、P4D 级别的页表）时无条件调用了 `pagetable_{pte,pmd,pud,p4d}_ctor()`。这些构造函数会执行以下关键操作：
- 设置 `page->page_type` 为 `PGTY_table`；
- 递增全局计数器 `NR_PAGETABLE`；
- 当内核配置了 `ALLOC_SPLIT_PTLOCKS` 时，还会为页表分配一个独立的 PTL（page table lock）。

然而，在内存热移除路径中，当通过 `free_hotplug_pgtable_page()` 释放这些由热移除操作腾出的页表页时，对应的析构函数 `pagetable_dtor()` 从未被调用。这导致两个直接后果：

1. **在开启 DEBUG_VM 且内核版本低于 v6.17（未包含清理 page_type 的 commit 2dfcd1608f3a9）时，会触发“Bad page state”警告**。原因是 `page->page_type` 与 `page->_mapcount` 共享 union，而 `page_type` 被设为 `f2(table)`（即 `PGTY_table`），使得释放检查时误认为 `_mapcount` 非零，从而打印错误信息并调用 `bad_page()`。Al

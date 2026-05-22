# mm/vmalloc: Extend page table walk to support larger page_shift sizes and eliminate page table rewalk

---

## 更新 - 2026-05-21 04:56 UTC

## 核心话题
该邮件是围绕 [PATCH v2 4/7] 的讨论，补丁旨在扩展 `vmap_pages_range_noflush_walk()`（原名 `vmap_small_pages_range_noflush()`），使其支持更大的 `page_shift` 值，并加入 PMD 级别映射以及 ARM64 上的 contiguous PTE 映射能力。关键的动机是消除 `vmalloc()` 在启用 `VM_ALLOW_HUGE_VMAP` 时，因使用 `vmap_range_noflush()` 逐页迭代而导致的**页表重复遍历（page table rewalk）**问题。补丁将这一路径统一到 `vmap_pages_range_noflush_walk()` 中，从而避免二次遍历带来的性能开销。

Mike Rapoport 在审阅后提出了一个设计层面的核心问题：此次修改之后，内核中存在两个极为相似的页表遍历器——`vmap_pages_range_noflush_walk()` 与 `vmap_range_noflush()`。两者在尝试创建巨型映射（huge mapping）的层级、页表修改的统计方式上存在细微差别，同时 `vmap_range_noflush()` 也未被赋予 contiguous 映射的支持。Mike 直接发问：“是否有一个根本性的理由需要保留两个页表遍历器？”以及“为什么不在 `vmap_range_noflush()` 中也支持 contiguous 映射？”。

Barry Song 在回复中解释了二者的本质差异：一种场景是为 `ioremap()` 服务，此时物理地址是完整连续的，一切可以简化处理，虽然已经支持大页映射，但本系列补丁仍通过更大的批量操作提升性能；另一种场景则是处理 `pages[]` 数组，其指向的物理页在整体上并不连续，必须在遍历数组时，尽力为那些物理连续的子集创建大映射（如 PMD 或 cont-PTE）。邮件在此处被截断，未完整展示后续论述。因此，讨论点集中在“两个遍历器的功能定位是否合理”与“是否应通过进一步统一代码来降低维护成本”上。

## 参与讨论人员
- Barry Song (baohua@kernel.org)  
- Mike Rapoport (rppt@kernel.org)  
- Wen Jiang (jiangwenxiaomi@gmail.com) — 原补丁作者

## 达成的结论
本次回复尚未形成明确共识。Barry Song 正在阐述保留两个独立遍历器的技术原因，但邮件因截断未能呈现完整论证以及 Mike 是否接受该解释。因此，讨论处于观点交换阶段，未看到最终结论。

## 下一步改进方向
1. Barry 需补充完整的理由，清楚说明为何不能用一套统一的遍历器同时高效服务“物理完全连续”和“物理不连续但可能局部连续”两种场景，或在哪些方面统一后会引入无法接受的复杂度或性能回退。
2. 若解释充分，可维持现有双遍历器设计，但需完善注释与文档，避免混淆。
3. 若审查者仍倾向统一，应考虑是否可抽象出一套核心遍历逻辑，通过回调或参数区分行为，同时补齐 `vmap_range_noflush()` 缺失的 contiguous 映射支持，并协调两种路径下的统计与批量操作差异。
4. 对新增的 PMD/cont-PTE 映射路径需加强测试，特别是 ARM64 平台上各种内存属性的组合场景。

## 新增补丁
在本邮件片段中未发布新的补丁版本。当前讨论基于 v2 系列的第 4 个补丁，未见 v3 或修订版。

---

## 更新 - 2026-05-22 13:31 UTC

## 核心话题
本补丁围绕 mm/vmalloc 子系统中页面映射路径的优化展开，重点关注如何统一小页与大页映射流程，并消除不必要的页表重遍历（page table rewalk）。当前 vmalloc 在 `vmap_range_noflush()` 中对于非 PAGE_SHIFT 的 `page_shift`（如 PMD 或 contiguous PTE）映射时，需要逐页遍历，导致二次遍历页表以确定映射方式，效率低下。补丁的核心思想是将原来的 `vmap_small_pages_range_noflush()` 函数重命名为 `vmap_pages_range_noflush_walk()`，并扩展其功能，使其能够处理 PMD 级以及连续 PTE 映射，从而将 small page 与大页的映射路径统一为“通过 struct page **pages 直接 PTE 迭代”的接口。这一改动避免了旧路径中先按小页处理再用 `vmap_range_noflush()` 划分大页时的重遍历开销。

具体实现上，补丁修改了 `vmap_pages_pte_range()`，增加了对 `shift` 参数的处理，利用 `vmap_set_ptes()` 批量设置 PTE，并计算步长更新计数器。同时，在 `__vmalloc_node_range_noprof()` 中，对于设置了 `VM_ALLOW_HUGE_VMAP` 的分配，不再使用 `vmap_range_noflush()` 逐个页映射，而是直接调用 `vmap_pages_range_noflush_walk()`，统一了小页和大页的入口。这样的设计简化了代码逻辑，消除了页表重建的冗余操作，提升了 vmalloc 映射路径的性能与可维护性。补丁还清理了相关注释和命名，明确表示现在这个 walk 函数处理的不再仅仅是“small pages”。

## 参与讨论人员
- Wen Jiang (Xiaomi)，邮箱 jiangwenxiaomi@gmail.com，补丁发送者
- Barry Song (Xiaomi)，邮箱 baohua@kernel.org，补丁作者
- Xueyuan Chen，邮箱 xueyuan.chen21@gmail.com，测试者

（本讨论线程仅包含此单一补丁提交，未见其他参与者回复）

## 达成的结论
当前邮件仅为补丁提交（PATCH v3 4/6），未发现回复或讨论记录，因此尚未形成任何结论或共识。需等待后续审核与反馈。

## 下一步改进方向
- 等待社区维护者（如 mm 或 vmalloc 相关子系统的维护者）审查代码逻辑、命名变更及对 page table walk 的影响。
- 可能需要对性能数据进行补充测试，以证明消除 rewalk 带来的实际收益。
- 确认 `vmap_set_ptes()` 在 ARM64 等架构上的连续 PTE 映射行为是否正确集成。
- 根据审核意见可能调整代码，例如进一步统一接口命名、处理异常情况等。

## 新增补丁
本邮件为补丁系列 v3 的第 4/6 个补丁，标题为 `mm/vmalloc: Extend page table walk to support larger page_shift sizes and eliminate page table rewalk`。该版本相对于之前的版本（v2）主要改动是：将 `vmap_small_pages_range_noflush()` 重命名为 `vmap_pages_range_noflush_walk()`，并在其中正式加入对 PMD 及连续 PTE 的支持，同时调整 `__vmalloc_node_range_noprof()` 中的调用，以实现统一映射路径并消除重遍历。

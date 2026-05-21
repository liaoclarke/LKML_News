# KVM: arm64: Reset page order in pKVM hyp_pool

---

## 更新 - 2026-05-21 15:33 UTC

## 核心话题
该补丁讨论的是在 pKVM（protected KVM）环境中的 hyp_pool（超visor 内存池）管理问题，具体涉及页面 `order` 字段的重置时机和方法。当一个受保护的 VM 开始初始化，其 stage-2 页表所需的 hyp_pool 已经预先初始化，如果后续 VM 初始化失败，就必须完整拆除这个 stage-2。拆除过程需要将池中每一页的 `refcount` 和 `order` 重置为 0。原来的代码在 `reclaim_pgtable_pages()` 中通过对整个池以 order-0 粒度进行分配来隐式地重置 order（如邮件中 `page->order = 0;` 显示），但在 VM 初始化错误路径中，被捐赠内存的物理地址（特别是 PGD）是已知的，完全没有必要遍历所有页面去重置。作者 Vincent Donnefort 认为 `vmemmap` 的 page order 是 hyp_pool 内部使用的字段，在池销毁时若不为 0 并不会直接导致问题，直到有另一个池要接纳该页时才需要是干净的。因此更合理的做法不是推迟到销毁时清空，而是在池再次初始化这一页时（`hyp_pool_init()`）将其 order 重置为 0。对于绕过 `hyp_pool_init()` 直接推入池的外部页面，由于无法信任其 order 值，而且这类页面从不参与合并（coalesce），就强制设为 order-0，保证安全插入。这一调整使得 `vmemmap` 的 order 字段除了 hyp_pool 内部再没有其他使用者，逻辑更清晰。补丁修复了由于 commit `256b4668cd89 ("KVM: arm64: Introduce separate hypercalls for pKVM VM reservation and initialization")` 引入的问题，该报告由自动化测试工具 Sashiko 给出。

## 参与讨论人员
- Vincent Donnefort (Google) —— 补丁提交者
- Sashiko (sashiko-bot@kernel.org) —— 问题报告者（自动化工具）

## 达成的结论
该邮件仅为一封补丁提交，未出现其他社区成员的回复与讨论，因此没有形成多人共识或结论。作者基于问题分析和代码审查，独立完成了这一改进并发布了 v3 版本补丁。

## 下一步改进方向
该补丁是系列补丁（v3）的第一个，后续还需要其他补丁配合完成完整修复。下一步需要：
1. 社区维护者和其他开发者对该系列展开代码审查，确认提交中的逻辑变更不会引入回归。
2. 确保相关的 pKVM 初始化与销毁路径的测试（尤其是错误路径）能覆盖该改动。
3. 需要将本改动与其他两枚配套补丁一并考虑（如 2/3 和 3/3），整体验证 VM 创建失败后资源回收的完整流程。

## 新增补丁
本邮件公布了补丁 **v3 1/3**，主要变更如下：
- 从 `guest_s2_zalloc_page()` 中移除对 `p->order = 0;` 的设置。
- 从 `reclaim_pgtable_pages()` 中移除重置 `page->order = 0;` 的逻辑。
- 将 order 重置移至 `hyp_pool_init()` 中，保证池初始化时页面 order 为 0。
- 对直接推入池的外部页面，强制将 order 设为 0，以避免后续被误用于合并操作。

# [RESEND v3 1/3] KVM: arm64: Reset page order in pKVM hyp_pool

---

## 更新 - 2026-05-21 15:36 UTC

## 核心话题
该讨论围绕 ARM64 pKVM（protected KVM）中 guest stage-2 页表管理的一个缺陷展开。当虚拟机初始化失败时，需要彻底拆除已经为其 stage-2 翻译分配的 hyp_pool 内存池。这要求将池中每一页的引用计数（refcount）和“阶数”（order，即连续页的数量级）还原为 0。原有的 `reclaim_pgtable_pages()` 函数通过以 order‑0 的方式分配整个池来隐式地重置 order，但在 VM 初始化错误路径上，已知道被捐赠内存（PGD）的具体地址，遍历所有页面并非必要，且可能引发效率或正确性问题。

提交者 Vincent Donnefort 指出，vmemmap 页面结构中的 order 字段是 hyp_pool 的私有字段，即使销毁 hyp_pool 时遗留了非零 order，在下一次另一个 pool 尝试接纳该页面之前并无实际危害。因此他改变了重置 order 的时机：从销毁阶段移至池初始化阶段 `hyp_pool_init()`。对于绕过 `hyp_pool_init()` 的“外部”页面（external pages），由于无法信任其 order 值，且这些页面从不合并为高阶块，补丁强制将其 order 设为 0，以保证安全插入池中。这样处理后，整个代码中不再有 hyp_pool 之外的地方使用 vmemmap 的 order 字段。

该补丁明确修复了提交 256b4668cd89（“KVM: arm64: Introduce separate hypercalls for pKVM VM reservation and initialization”）引入的问题，并由内核自动测试机器人 sashiko-bot 报告。技术核心在于精确管理 hyp_pool 页面元数据，避免因残留的非零 order 导致后续页面分配或合并错误，体现了对受保护虚拟化环境中内存生命周期和元数据一致性的重视。关键代码变更集中在 `guest_s2_zalloc_page()`、`reclaim_pgtable_pages()` 以及 `hyp_pool_init()` 等函数中，移除了冗余的 order 归零操作，将其统一收敛至池初始化与外部页面处理点。

## 参与讨论人员
- Vincent Donnefort，Google（补丁提交者）
- Sashiko（内核自动化测试 bot，报告了该问题，但通常不视为人类讨论参与者）

## 达成的结论
该邮件为单独的补丁提交（v3 重发），线程中尚未出现其他维护者或开发者的评审意见、质疑或赞同。因此尚未达成社区层面的共识，作者提供的修复方案等待进一步审阅。

## 下一步改进方向
- 需经 ARM64 KVM 维护者（如 Marc Zyngier、Oliver Upton 等）审阅该补丁，确认 order 重置逻辑迁移到 `hyp_pool_init()` 是否在所有场景下均正确，特别是与外部页面交互的边界情况。
- 验证对 VM 初始化失败路径的简化是否真的安全，避免因不再遍历全池而遗漏某些页面的 refcount/order 清理。
- 该补丁为系列 v3 的第 1/3 部分，需要结合后续补丁完整评估；测试要求覆盖正常 VM 创建、销毁以及初始化中途失败等场景，确保 pKVM 内存管理无回归。

## 新增补丁
本线程仅包含一封邮件，即 [RESEND v3 1/3] 补丁，是之前 v3 版本的重发，未附加任何较此更新的补丁版本。

---

## 更新 - 2026-05-22 07:53 UTC

## 核心话题
本补丁针对 pKVM（protected KVM）中 hyp_pool 页面管理的一个疏忽进行修复。在受保护的 KVM 虚拟化场景下，每个虚拟机的 Stage-2 页表由 hyp_pool 管理，其页面在 vmemmap 中会记录 `order` 字段，表示页面的大小阶数。如果 VM 初始化失败，需要拆解已分配的 Stage-2 hyp_pool。原有代码在回收页表页面时，通过 `reclaim_pgtable_pages()` 以 order-0 粒度遍历整个池来隐式重置页面 order，但在 VM 初始化错误路径中，捐出的内存地址（即 PGD 地址）是已知的，完全遍历池中所有页面不仅多余，也会带来不必要的开销。

更严重的是，非零的 `order` 字段如果未被正确重置，虽然对当前已销毁的 hyp_pool 无害，但若该物理页随后被另一个 hyp_pool 接纳，残留的 order 值可能导致页合并或分配逻辑错误。补丁采取的思路是：将 vmemmap 的 order 重置从销毁阶段移至初始化阶段，即在 `hyp_pool_init()` 中统一重置 order 为 0。对于绕过 `hyp_pool_init()` 直接插入的“外部”页面，由于当前代码从不对外部页面进行合并，因此直接强制 order-0 以保证安全插入。这样处理之后，vmemmap order 字段的修改完全被约束在 hyp_pool 内部，消除了潜在的跨界影响。

补丁内容体现在两块：移除 `guest_s2_zalloc_page()` 中对 `p->order = 0` 的设值，因为该函数用于分配新页面，此时 order 本该为 0 无需重复设置；在 hyp_pool 初始化入口处显式重置 order，同时在处理外部页面时强制 order 为 0。该变更修复了由 commit 256b4668cd89（"KVM: arm64: Introduce separate hypercalls for pKVM VM reservation and initialization"）引入的问题，并由内核测试机器人 Sashiko 报告。

## 参与讨论人员
- Vincent Donnefort (Google) — 补丁作者
- Fuad Tabba (Google) — 审阅者及测试者
- Sashiko (sashiko-bot@kernel.org) — 问题报告者（自动化测试机器人）

## 达成的结论
已达成共识。Fuad Tabba 对该补丁提供了 `Reviewed-by` 和 `Tested-by` 标签，表明补丁通过审查且经过测试，没有遗留的技术分歧。该补丁可以进入后续合并流程。

## 下一步改进方向
该补丁是 `[RESEND v3 1/3]` 系列的一部分，后续需等待同一系列其他补丁（如 2/3、3/3）的审查与合并；此外，相关的 pKVM 维护者（如 Marc Zyngier、Oliver Upton）需要最终确认并合入 arm64 或 KVM 树。如果有自动化测试（如 Sashiko 机器人），可以进行回归验证以确保问题被彻底解决且无新问题引入。

## 新增补丁
本邮件线程中未出现新版本补丁，当前讨论基于重发的 v3 版本，未产生 v4 或后续修订。

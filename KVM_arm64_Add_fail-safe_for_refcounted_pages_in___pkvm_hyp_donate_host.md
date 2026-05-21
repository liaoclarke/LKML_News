# KVM: arm64: Add fail-safe for refcounted pages in __pkvm_hyp_donate_host

---

## 更新 - 2026-05-21 14:07 UTC

## 核心话题

本邮件讨论的补丁旨在增强 pKVM（protected KVM）的 **页状态机可靠性**。作者 Vincent Donnefort 指出，之前在 `__pkvm_init_vm` 的错误路径中发现了一个 bug，可能导致 hypervisor 泄漏 refcount 不为零的页面——即页面虽然仍被引用，但 hypervisor 已经失去了对它的管理权，这直接威胁到 pKVM 的状态机（state machine）正确性。

补丁的核心思路是在 `__pkvm_hyp_donate_host` 函数中引入一层 **fail-safe 检查**：在将页面从 hypervisor 状态转为无状态（PKVM_NOPAGE）并最终捐献给 host 之前，新增一个 helper `__hyp_check_page_count_range`，遍历范围内每一页，若 `page->refcount != 0` 则返回 `-EBUSY`，从而阻止捐献操作，避免泄漏处于引用中的页面。

补丁同时重构了 `__pkvm_host_unshare_hyp` 中原有的 open-coded 检查，将其统一替换为新 helper，消除了 `hyp_page_count((void *)virt)` 的临时局部变量，使代码更整洁。

关键引用如下：
- 提交说明阐述动机：“A previous bug in __pkvm_init_vm error path showed that the hypervisor could leak refcounted pages, (i.e. losing access to a page while its refcount is still elevated). This poses a threat to the pKVM state machine.”
- 性能考量：“Transitions are not a hot path so added security is worth the extra check.” 由于页面状态转换并非热路径，增加的检查开销可以接受，换来更高的安全性。

## 参与讨论人员

- **Vincent Donnefort** (vdonnefort@google.com) — 补丁作者。
- **Fuad Tabba** (tabba@google.com) — 审查者，给出了 Reviewed-by 和 Tested-by。

## 达成的结论

达成共识，补丁整体上获得认可。Fuad Tabba 给出了 **Reviewed-by** 和 **Tested-by** 标签，意味着从代码逻辑和功能测试层面均无问题。唯一注意的是 commit message 中一处笔误：在“introducing a fail-safe in n __pkvm_hyp_donate_host”里多了一个字符 'n'（原文为“in n __pkvm_hyp_donate_host”），Fuad 评论“Stray n.”，后续需修正这一拼写错误即可采纳。

## 下一步改进方向

- 修正 commit message 中的 stray 'n' 笔误（去掉多余的 'n'），确保描述准确。
- 无其他功能或实现层面的修改要求，补丁经修正后可直接合并。

## 新增补丁

本线程中发布了补丁的 **v2 版本**：

- **v1**（最初作为 [PATCH 2/2]）存在，但在线程中未直接出现其完整内容，只是后续 v2 提到了对同一功能的改进。
- **v2**（[PATCH v2 3/3]）是本线程直接贴出的新版本，主要变化是引入统一的 helper `__hyp_check_page_count_range`，并替换了 `__pkvm_host_unshare_hyp` 中的重复检查，使 `__pkvm_hyp_donate_host` 也统一使用该 helper 完成 refcount 检查。v2 与 v1 的核心逻辑一致，但代码结构更清晰。

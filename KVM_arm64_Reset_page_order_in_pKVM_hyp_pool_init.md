# KVM: arm64: Reset page order in pKVM hyp_pool_init

---

## 更新 - 2026-05-21 14:30 UTC

## 核心话题
本邮件讨论围绕 Linux 内核 ARM64 架构下 pKVM（保护模式 KVM）内存管理中的一个缺陷修复。当 VM 初始化失败，且其 Stage‑2 页表的 hyp_pool 已经完成初始化时，需要彻底销毁该 Stage‑2 页表。这就要求将池中所有页面的 `refcount` 和 `order` 字段重置为 0。

当前代码在 `reclaim_pgtable_pages()` 中通过 **order‑0 粒度分配整个池** 来隐式重置 `order`，但在 VM 初始化的错误路径中，捐赠内存（PGD）的地址是已知的，因此不必遍历池中所有页面。Vincent Donnefort 指出：

> *“Since the vmemmap page order is a hyp_pool‑specific field, leaving a non‑zero order on hyp_pool destruction is harmless until another pool attempts to admit the page.”*  
> （由于页面的 order 是 hyp_pool 专属字段，在池销毁时保留非零 order 并不会造成危害，直到另一个池尝试接纳该页面。）

因此，他将重置逻辑从池销毁（`reclaim_pgtable_pages`）移至池初始化（`hyp_pool_init`）阶段，可以在初始化时一次性将初始池范围内所有页面的 `order` 清零。对于池初始化后动态添加的页面（例如通过 `guest_s2_zalloc_page()`），仍需手动管理其 order。

补丁还添加了一个 `WARN_ON()`，在 hyp_pool 的页面附着路径中检查页面 order 是否超过了池的 `max_order`，以便及时发现异常。该修复针对的提交是 `256b4668cd89`（"KVM: arm64: Introduce separate hypercalls for pKVM VM reservation and initialization"），由自动化测试工具 Sashiko 发现并报告。

技术动机在于：**避免在 VM 初始化失败时对页面进行不必要的遍历**，同时将 order 重置的职责明确集中到池初始化中，使代码更清晰，并防止后续其他池重复使用该页面时因遗留 order 值而产生错误。WARN_ON 则提供了额外的防御性检查。

## 参与讨论人员
- **Vincent Donnefort** <vdonnefort@google.com>（补丁作者，Google）
- **Fuad Tabba** <tabba@google.com>（审阅者，Google）
- **Sashiko** <sashiko-bot@kernel.org>（自动化测试/报告工具，原始问题报告者）

## 达成的结论
从现有邮件片段看，尚未形成明确共识。Fuad Tabba 对补丁作出了回复（邮件被截断，仅显示了补丁 diff 的引用部分），随后 Vincent 再次回复（同样被截断）。回复片段并未包含 Acked‑by 或 Reviewed‑by 标签，说明双方仍在沟通中，可能 Fuad 提出了某些疑问或需要进一步澄清。由于双方均来自 Google，通常容易达成一致，但当前状态仍属“讨论进行中”，未有最终结论。

## 下一步改进方向
1. **回应审阅意见**：Vincent 需要根据 Fuad 的评论（可能隐藏在截断部分）对代码进行解释或调整。
2. **代码逻辑验证**：
   - 确认 `hyp_pool_init()` 中的 order 重置能够覆盖所有页面重新使用的场景，尤其是当页面被回收并加入其他池时。
   - 确保 `WARN_ON` 的触发条件准确，不会在正常流程中产生误报。
3. **测试**：
   - 专门测试 VM 初始化失败路径，验证页面 order 和引用计数完全重置，无内存泄漏或损坏。
   - 回归测试加入动态分配页面的场景，确保手动 order 管理未受影响。
4. 如果 Fuad 要求改动，可能需要发布 **v3** 系列补丁。

## 新增补丁
本线程中发布了 **v2 系列补丁的第 1/3 部分**：
- **`[PATCH v2 1/3] KVM: arm64: Reset page order in pKVM hyp_pool_init`**
  - **变更内容**：将页面 order 重置操作从 `reclaim_pgtable_pages()` 移除，改为在 `hyp_pool_init()` 中统一处理；在 hyp_pool 页面附着路径添加 `WARN_ON` 以检测异常 order；更新相关代码路径。
  - **状态**：待审阅，尚未收到明确的

# mm: Add ptep_try_set() for lockless empty-slot installs

---

## 更新 - 2026-05-20 13:50 UTC

## 核心话题
本邮件是 Tejun Heo 提交的补丁系列第 1/8，目的是为 ARM64 和 x86 架构新增一个 `ptep_try_set()` 函数。该函数提供了一种无锁的、原子的页表项（PTE）空槽安装操作：只有当目标 `pte_t *` 当前为 `pte_none()` 时，才将其原子地设置为 `new_pte`，成功返回 `true`，否则返回 `false`。若架构未提供实现，则通用版本直接返回 `false`。

技术动机源于 BPF arena 的内核端故障恢复路径。BPF 程序可能在持有 arena 自旋锁（`raw_res_spin_lock_irqsave`）的情况下触发缺页异常，此时若使用常规的试锁-重试机制会导致 A-A 死锁，因此必须采用无锁的 cmpxchg 方式安装页表项。作者明确指出该辅助函数仅限于特殊的内核页表，这些页表由合作写入者通过原子访问器协调并发，不适用于通用用户空间页表。

补丁为 ARM64 和 x86 提供了基于 `try_cmpxchg` 的覆盖实现：
- ARM64 版本直接对 `pteval_t` 做 `try_cmpxchg`，比较值为 0（即空槽）。
- x86 版本类似（邮件中截断，但可从结构推断）。

代码节选：
```c
static inline bool ptep_try_set(pte_t *ptep, pte_t new_pte)
{
    pteval_t old = 0;
    return try_cmpxchg(&pte_val(*ptep), &old, pte_val(new_pte));
}
#define ptep_try_set ptep_try_set
```

v2 版本根据 David Hildenbrand 和 Alexei Starovoitov 的建议，将函数重命名为 `ptep_try_set()`，并完善了内核文档，强调其仅适用于内核 PTE 场景。这一改动使函数名更准确地反映了“尝试设置”的语义，且与现有 `ptep_set()` 等命名风格保持一致。

## 参与讨论人员
- **Tejun Heo** (tj@kernel.org) — 补丁作者，来自 Meta / Linux 内核社区。
- **Kumar Kartikeya Dwivedi** (memxor@gmail.com) — 提供原始建议。
- **Alexei Starovoitov** (ast@kernel.org) — 提供建议，来自 Meta / BPF 维护者。
- **David Hildenbrand** (david@kernel.org) — 审核并提供命名与文档建议，来自红帽。

由于该邮件仅为补丁提交，尚未有后续回复，因此当前无更多交互参与者。

## 达成的结论
本邮件为补丁 v2 版本的提交，未包含后续讨论内容，因此尚无最终共识。从补丁描述可推断，v1 版本已获得初步反馈并被作者采纳，修改为当前提交的 v2。目前该补丁处于待审查状态，需等待架构维护者（ARM64: Catalin Marinas/Will Deacon, x86: Ingo Molnar/Peter Anvin 等）和 BPF 子系统维护者的进一步审查与 Ack。

## 下一步改进方向
1. **架构审核**：需 ARM64 和 x86 维护者确认新增的 `ptep_try_set` 实现是否与各自的内存模型、原子性要求完全一致，尤其是在乱序执行和缓存一致性方面的安全性。
2. **BPF 子系统集成**：后续的 BPF arena 补丁需要实际调用该函数，并证明其在实际锁竞争场景下能避免死锁且性能可靠。
3. **其他架构的考量**：当前仅 ARM64 和 x86 提供了实际实现，其他架构留空。若未来其他架构也需要内核端 BPF arena 功能，可能需要补充各自的高效实现。
4. **测试加固**：需在 CONFIG_BPF_ARENA 测试场景下进行充分压力测试，验证并发下的正确性，并确保“fallback to oops”路径在其他架构上行为符合预期。
5. **文档完善**：可能需要在内核内存管理文档中明确记录 `ptep_try_set()` 的适用范围和约束，以避免误用于通用用户页表。

## 新增补丁
本邮件为 **v2** 版本的 [PATCH 1/8]。相较于 v1 的主要变动：
- 函数名从最初的命名（未在邮件中提及）更改为 `ptep_try_set()`；
- 收紧 kerneldoc，明确指出该函数专用于内核 PTE 的并发安装，并说明调用者必须保证操作在特殊内核页表上进行；
- 规范了定义方式（使用 `#define ptep_try_set ptep_try_set` 供通用头文件条件包含）。

未在此线程中发布更新的版本，当前仅此 v2 提交。

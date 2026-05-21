# [RESEND v3 3/3] KVM: arm64: Add fail-safe for refcounted pages in __pkvm_hyp_donate_host

---

## 更新 - 2026-05-21 15:36 UTC

## 核心话题
该邮件讨论的是针对 pKVM（protected KVM）中 hypervisor 内存管理的一个安全加固补丁。Vincent Donnefort 指出，此前在 `__pkvm_init_vm` 的错误处理路径中曾发现一个缺陷，可能导致 hypervisor 泄漏“引用计数页面”（refcounted pages），即虽然丢失了对页面的访问权，但其引用计数仍未归零。这种状态会破坏 pKVM 状态机的完整性，例如可能导致后续的页面状态转换出现不可预期的行为，或在宿主与 hypervisor 之间共享页面时产生安全漏洞。

为消除这一威胁，补丁在 `__pkvm_hyp_donate_host` 中引入了一个 fail‑safe 检查。该函数负责将 hypervisor 拥有的页面归还（donate）给宿主，是页面所有权转换的关键路径。虽然这类转换并非热路径，但作者认为“增加的检验开销在安全性面前是值得的”（Transitions are not a hot path so added security is worth the extra check.）。

具体实现上，补丁新增了辅助函数 `__hyp_check_page_count_range`，遍历指定物理地址范围内的所有页面，检查其 `refcount` 成员是否为零，若任一页面引用计数非零则返回 `-EBUSY`。在 `__pkvm_hyp_donate_host` 获取宿主锁并完成页面状态范围检查后，立即调用这一新函数进行引用计数校验。同时，该补丁也对 `__pkvm_host_unshare_hyp` 做了语义相同的重构：用新的范围检查函数替代原先内联的 `hyp_page_count` 逐页检查，并顺带移除了一个未使用的局部变量 `virt`。这样既统一了校验逻辑，又避免了代码重复。

补丁已获得 Fuad Tabba 的 `Reviewed-by` 和 `Tested-by` 标签，表明其已通过审查和功能验证。

## 参与讨论人员
- Vincent Donnefort (Google) —— 补丁作者  
- Fuad Tabba (Google) —— 审查者与测试者  

该邮件为独立补丁提交，未见其他参与者回复，尚未形成多轮讨论。

## 达成的结论
由于当前仅为补丁投递邮件，尚无后续讨论或回复，因此未形成明确共识。但补丁已带有 review 和 test 标签，表明它已处于可被接纳的状态，等待维护者将其合入对应代码树。

## 下一步改进方向
1. 等待 arm64 KVM 维护者（如 Marc Zyngier、Will Deacon 等）的审阅与最终合并。
2. 考虑到这是 v3 系列的第三部分，可能需要确保前序依赖补丁也一同被接受，或确认该补丁可以独立应用。
3. 若合入后在实际场景中触发 `-EBUSY`，需进一步调查引用计数泄漏的真正根因，而非仅依赖 fail‑safe 拦截。
4. 可以考虑为相关路径增加更详细的测试用例，覆盖引用计数非零时 donate 操作被拒绝的场景。

## 新增补丁
本次讨论中包含一个补丁版本：
- **[RESEND v3 3/3] KVM: arm64: Add fail-safe for refcounted pages in __pkvm_hyp_donate_host**  
  与前版 v3 相比主要改动为resend，代码内容无变化。该补丁在 `mem_protect.c` 中新增 `__hyp_check_page_count_range`，并在 `__pkvm_hyp_donate_host` 和 `__pkvm_host_unshare_hyp` 中引入引用计数范围检查。

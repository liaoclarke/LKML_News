# KVM: arm64: Fix memory leak in hyp_trace_unload()

---

## 更新 - 2026-05-21 13:46 UTC

## 核心话题
该邮件来自 Vincent Donnefort（Google），是修复 KVM arm64 架构下 hyp trace 子系统内存泄漏问题的补丁（v2 3/3）。问题的根源在于 `hyp_trace_load()` 在为 trace buffer 分配描述符页面（descriptor pages）时，虽然成功分配了内存，但忘记将所分配的大小记录到 `trace_buffer->desc_size` 字段中。这导致后续调用 `hyp_trace_unload()` 进行卸载时，会调用 `free_pages_exact(trace_buffer->desc, trace_buffer->desc_size)` 尝试释放描述符页面，但由于 `desc_size` 仍为未初始化的值（实际表现为 0），`free_pages_exact()` 以大小为 0 进行释放，从而无法真正回收此前分配的物理内存页面，造成内存泄漏。

邮件明确指出该缺陷由 `3aed038aac8d ("KVM: arm64: Add trace remote for the nVHE/pKVM hyp")` 提交引入，并由 Sashiko 自动化工具 `sashiko-bot@kernel.org` 报告。修复方案非常直接：在 `hyp_trace_load()` 中成功分配描述符页面后，将计算好的 `desc_size` 赋值给 `trace_buffer->desc_size`；同时在 `hyp_trace_unload()` 中释放内存后，将 `trace_buffer->desc_size` 清零并将 `desc` 指针置空，以保持结构体状态的一致性并避免悬空指针。

从补丁修改的代码片段（arch/arm64/kvm/hyp_trace.c）可以看到：
- 在 `hyp_trace_load()` 的第 249 行附近，`trace_buffer->desc = desc;` 之后增加 `trace_buffer->desc_size = desc_size;`。
- 在 `hyp_trace_unload()` 的第 298 行附近，调用 `free_pages_exact()` 之后，增加 `trace_buffer->desc_size = 0;`。

该修复不仅解决了内存泄漏问题，还使 descriptor 大小信息得到妥善维护，可能用于后续调试或状态检查，确保 hyp trace 模块的资源管理更加健壮。因为 trace buffer 是在 remote 加载过程中（例如从 host 向 pKVM/nVHE 端加载）动态分配的，如果描述符页面没能正确释放，会导致内存逐渐耗尽，在长期运行的虚拟化场景下尤为危险。补丁提交者使用了 `Fixes:` 标签明确回溯到引入该漏洞的提交，方便后续维护者进行稳定版内核的回合。

## 参与讨论人员
- Vincent Donnefort (vdonnefort@google.com) — Google

## 达成的结论
本邮件仅为一封独立的补丁提交，未在讨论串中出现任何回复或后续讨论，因此尚未在社区内达成明确的审查结论或共识。补丁本身逻辑清晰，属于“显而易见”的错误修复，预计在后续版本中会被合并，但该结论并非来自邮件内容的讨论。

## 下一步改进方向
- 该补丁需要经过 ARM64 KVM 子系统的维护者（如 Marc Zyngier, Oliver Upton 等）的 Review 和 Ack。
- 可能需要进行回归测试，确保 trace 的加载/卸载流程不再泄漏内存，并且不影响正常 tracing 功能。
- 如无异议，补丁有望被合入 `kvmarm/next` 分支，并可能在后续稳定更新中回植到受影响的长期支持内核版本。

## 新增补丁
该邮件中提交了 `[PATCH v2 3/3] KVM: arm64: Fix memory leak in hyp_trace_unload()`，此补丁为 v2 版本的第 3 个补丁。相比前一版本的可能变化未在邮件中说明，但代码改动集中在 `arch/arm64/kvm/hyp_trace.c`，具体包括：
- 在 `hyp_trace_load()` 中增加 `trace_buffer->desc_size = desc_size;`
- 在 `hyp_trace_unload()` 中增加 `trace_buffer->desc_size = 0;`

这两处改动构成了本次补丁的完整修复。

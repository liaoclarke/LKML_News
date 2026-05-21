# arm64: RME: Handle Granule Protection Faults (GPFs)

---

## 更新 - 2026-05-21 16:15 UTC

## 核心话题
该邮件讨论的是 ARM64 架构下 Realm Management Extension（RME）中 Granule Protection Fault（GPF）的处理实现，属于 v14 系列补丁第 3/44 号。RME 引入了“领域”（Realm）概念，主机若访问已被委派给领域的物理页（granule），硬件会触发 GPF。补丁在 `arch/arm64/mm/fault.c` 中新增两个处理函数：`do_gpf_ptw` 和 `do_gpf`。其中，页表遍历（PTW）期间发生的 GPF 被认为是内核严重错误，直接调用 `die_kernel_fault` 触发 oops；而非 PTW 的 GPF 则可能由用户空间对已委派页的非法访问引起，补丁通过 `fixup_exception` 尝试恢复，若无法恢复则返回 1，让上层逻辑向用户进程发送 `SIGBUS`，以便调试。

从变更记录中可以看到，自 v10 起处理方式发生了重要变化：不再调用 `arm64_notify_die()`，而是简化成直接返回 1。这很可能是根据社区（特别是 Marc Zyngier）的反馈所做的修改，因为 Marc 曾在之前的评审中提出避免过于复杂的 die 通知机制，主张在非致命路径上使用更轻量的错误报告。邮件片段中 Marc 的原始评论被截断，但 Steve Price 的回复表明这一调整已被接受并反映在 v14 中。该补丁已获得 Suzuki K Poulose 和 Gavin Shan 的 `Reviewed-by` 标签，说明代码本身在技术层面已获得相当程度的认可。整个讨论聚焦于错误处理策略的简化，既保证了内核在面对严重错误时的诊断能力，又避免了在不必要的情况下引入重量级内核 panic 机制，体现了主线内核在安全扩展与易用性之间的平衡。

## 参与讨论人员
- Steven Price (steven.price@arm.com) — 补丁提交者，ARM 工程师
- Marc Zyngier (maz@kernel.org) — 评论者，内核维护者（中断子系统、KVM/arm64），可能使用 Google 或 ARM 邮箱
- Suzuki K Poulose (suzuki.poulose@arm.com) — 审查者，ARM 工程师
- Gavin Shan (gshan@red

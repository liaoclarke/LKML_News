# sched_ext: Convert ops.set_cmask() to arena-resident cmask

---

## 更新 - 2026-05-21 00:19 UTC

## 核心话题
本邮件线程围绕 Linux 内核 sched_ext（可扩展 BPF 调度器）中 `ops.set_cmask()` 操作的实现优化展开。原实现中，内核侧无法直接写入 BPF arena 内存，因此当调用 `ops.set_cmask()` 时，需要在内核内存中先将 `cpumask` 转换为 `cmask` 结构体，然后将该内核内存指针传递给 BPF 程序。BPF 侧为了能够使用 arena 原生的 cmask 辅助函数，不得不通过 `cmask_copy_from_kernel()` 逐字读取（probe-read）内核内存中的 cmask，再复制到 arena 区域中。这种方式虽然功能正确，但非常笨拙且增加了不必要的开销。

随着内核侧直接访问 arena 能力的引入（通过 dual mapping 机制提供 `kern_va`），本补丁将 `cmask` 的构建直接置于 arena 内存中。内核通过 dual mapping 的 `kern_va` 指针写入 arena，而 BPF 程序则通过 `__arena` 指针直接解引用，如同操作其他 arena 数据结构一样。具体实现中，每个 CPU 在 `sch->set_cmask_scratch` 中保存了一个 arena 区域的 `kern_va` 指针，调用时通过 `bpf_arena_map_kern_vm_start()` 计算出对应的用户态地址（uaddr），传递给 BPF 的 `set_cmask` 回调。由于调用者持有 rq 锁且中断已禁用，保证了每 CPU 暂存区的独占访问。

补丁删除了不再需要的 `cmask_copy_from_kernel()` 和相关 `scx_set_cmask_scratch` 等旧代码，净删除 80 行，新增 75 行，整体简化了调用路径，提升了性能与可维护性。

## 参与讨论人员
- Tejun Heo (tj@kernel.org) —— 补丁作者，来自 kernel.org。
- Emil Tsalapatis (emil@etsalapatis.com) —— 审阅者，提供了 Reviewed-by 标签。

## 达成的结论
已达成共识。Emil Tsalapatis 在回复中给出了 `Reviewed-by: Emil Tsalapatis <emil@etsalapatis.com>`，表明其认可该补丁的正确性与设计方向。邮件中没有进一步的反对意见或修改要求，补丁被认为可以接受。

## 下一步改进方向
该补丁为系列补丁（8/8）的最终部分，下一步应当是整合所有审阅标签，等待维护者将整个补丁集合纳入 sched_ext 开发分支（或相应的内核树）。可能需要通过完整的 sched_ext 测试套件及 BPF arena 相关 selftest 验证，确保没有引入性能衰退或并发问题。此外，后续如有调度器开发者需要对 `set_cmask` 进行进一步扩展，可直接利用此新机制。

## 新增补丁
本次邮件中仅包含原补丁（PATCH 8/8），未发布新版本。补丁版本为初始提交版本，Emil Tsalapatis 的 Reviewed-by 是针对该版本的。如后续因合并冲突或测试反馈而调整，可能产生 v2，但当前线程内未出现新版本。

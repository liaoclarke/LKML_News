# sched_ext: Sub-allocator over kernel-claimed BPF arena pages

---

## 更新 - 2026-05-20 13:50 UTC

## 核心话题
这封邮件是 Tejun Heo 提交的 sched_ext（可扩展调度类）补丁系列中的第 7 个补丁，主题为“在由内核声明（claimed）的 BPF arena 页面上构建子分配器”。该补丁并非直接讨论 ARM64 架构，而是为 sched_ext 框架增加一套内存管理设施。

核心技术点是：在 BPF arena（一种 BPF 与内核共享的大块连续虚拟地址空间）中，之前可能已经注册了内核可以使用的页面。本补丁在此基础上构建一个基于 gen_pool 的通用子分配器，供后续的内核管理结构（例如每个 CPU 的 set_cmask 掩码）从这个池中分配存储空间。关键函数包括：
- `scx_arena_pool_init()` 创建 gen_pool。
- `scx_arena_alloc()` 返回内核虚拟地址。当池耗尽时，通过 `bpf_arena_alloc_pages_sleepable()` 声明更多页面来扩容。分配的内存在内核侧映射地址添加，调用者如需 BPF arena 视角的地址需自行转换。
- 分配操作允许睡眠（GFP_KERNEL），因为当前所有使用者都在 enable 路径中运行（ops.init() 之后、validate_ops() 之前），睡眠是安全的。
- `scx_arena_pool_destroy()` 遍历所有块，用 gen_pool_free() 归还范围，然后销毁 gen_pool。底层 arena 页面在 arena 映射销毁时释放，所以池销毁时不显式释放页面。

代码新增了 `kernel/sched/ext_arena.c` 和 `kernel/sched/ext_arena.h`，在构建文件中加入 `genalloc.h`、`find.h` 等头文件。此补丁作为系列中“内核管理 arena 结构”的基础，为后续将调度状态数据直接放在 BPF arena 中、从而更高效地在 BPF 和内核之间共享数据铺路。

## 参与讨论人员
- Tejun Heo <tj@kernel.org>（补丁作者）

邮件线程中仅出现了补丁提交，没有其他回复或讨论参与者。

## 达成的结论
本邮件为一封补丁提交，并非讨论线程，因此目前尚不存在讨论共识或结论。补丁尚处于等待审查和反馈的阶段。

## 下一步改进方向
1. 需要获得社区（尤其是 sched_ext 和 BPF 维护者）的审查 Ack 或意见。
2. 可能需要根据审查建议调整接口设计（如睡眠分配的安全性、与 BPF arena 生命周期绑定的正确性）。
3. 在后续补丁中提供实际使用者（例如 per-CPU set_cmask），以验证子分配器功能。
4. 确认翻译地址的调用者约定是否清晰，是否需要提供辅助宏来统一内核 VA 与 BPF arena 偏移的转换。

## 新增补丁
本补丁为系列中的第 7 版，即 `[PATCH 7/8] sched_ext: Sub-allocator over kernel-claimed BPF arena pages`。邮件中未给出更详细的版本变更记录，仅包含此次提交的完整代码差异。

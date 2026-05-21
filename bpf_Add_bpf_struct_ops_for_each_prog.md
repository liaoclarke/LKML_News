# bpf: Add bpf_struct_ops_for_each_prog()

---

## 更新 - 2026-05-20 13:50 UTC

## 核心话题
本邮件是 Tejun Heo 向 Linux 内核社区提交的补丁系列中的第 4/8 号补丁，标题为《bpf: Add bpf_struct_ops_for_each_prog()》。补丁的核心目标是在内核 BPF 子系统（bpf_struct_ops）中新增一个辅助函数 `bpf_struct_ops_for_each_prog()`，用于遍历某个 struct_ops 映射实例中包含的所有 BPF 程序（即成员 prog）。  

技术背景：struct_ops 允许用户以 BPF 程序的形式实现内核预定义的操作表（如调度器、TCP 拥塞控制等）。当 struct_ops 的 `->reg()` 回调（注册回调）被调用时，内核可能需要检查已加载的 BPF 程序，例如发现它们引用了哪些 BPF 映射（maps）。补丁描述中明确指出：“struct_ops ->reg() callbacks (and similar) sometimes need to inspect the loaded BPF programs, e.g. to discover maps they reference via prog->aux->used_maps.”  

实现方式：新函数通过 `container_of(@kdata)` 反向推导出包含该 `kdata` 虚表（vtable）的 `bpf_struct_ops_map` 结构体，然后遍历 `st_map->links[i]->prog`，其中 `i` 从 0 到 `funcs_cnt`（成员函数数量）。补丁特别强调这种访问模式与已有的 `bpf_struct_ops_id()` 相同，不需要额外的锁保护，因为在 `->reg()` 被调用时 `st_map` 已经完全填充并保持稳定（“st_map is fully populated and stable”）。  

直接推动此补丁的用例是 sched_ext（可扩展调度器）。Tejun Heo 在补丁描述中写道：“A sched_ext follow-up walks the member progs of a cid-form scheduler's struct_ops map, reads prog->aux->arena directly, and requires all member progs to reference exactly one arena, without requiring the BPF program to call a registration kfunc.” 这意味着在 sched_ext 的具体实现中，需要遍历 struct_ops 映射的所有成员 BPF 程序，直接读取 `prog->aux->arena` 并断言这些程序都引用完全相同的 arena（BPF 内存区域），从而免去由 BPF 程序主动调用注册 kfunc 的繁琐步骤。这为构建更简洁、强制一致的调度器模型提供了基础设施。  

补丁本身只添加了函数声明（include/linux/bpf.h）和实现（kernel/bpf/bpf_struct_ops.c），并标记为 `EXPORT_SYMBOL_GPL`，以便后续模块调用。

## 参与讨论人员
- Tejun Heo <tj@kernel.org>（补丁提交者，来自内核社区，主要负责 cgroup、workqueue 等子系统，近期也活跃于 sched_ext）

（此邮件线程仅包含这一封提交邮件，未出现其他回复或讨论者。）

## 达成的结论
该邮件为独立的补丁提交，无任何后续回复或讨论，因此未形成任何共识或结论。补丁处于待审阅状态，尚未被合并或拒绝。

## 下一步改进方向
由于没有社区反馈，下一步主要需要：
- 等待 BPF 维护者或其他相关子系统的开发者审阅此补丁，确认其接口合理性与安全性。
- 验证该辅助函数在 sched_ext 等后续使用者中是否能正确工作，特别是遍历所有成员 prog 时不会遗漏或越界。
- 确认补丁中“no new locking”的假设在所有 struct_ops 实现中均成立，避免潜在的并发问题。
- 可能需要对 `bpf_struct_ops_for_each_prog()` 的回调逻辑和参数语义进行文档化，使其更易被其他子系统复用。

## 新增补丁
本邮件线程中仅包含一份补丁，即 `[PATCH 4/8] bpf: Add bpf_struct_ops_for_each_prog()`。无后续新版本出现。该补丁是 8 件系列中的第 4 件，其余补丁可能涵盖 sched_ext 的整体支持以及其他准备性改动。

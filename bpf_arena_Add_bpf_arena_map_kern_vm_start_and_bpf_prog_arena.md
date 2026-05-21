# bpf/arena: Add bpf_arena_map_kern_vm_start() and bpf_prog_arena()

---

## 更新 - 2026-05-21 00:08 UTC

## 核心话题
本邮件讨论的补丁（PATCH 5/8）旨在为 Linux 内核的 BPF 子系统新增两个访问 arena 结构的辅助函数，以打破 `struct bpf_arena` 对 arena.c 外部调用者的不透明性。补丁作者 Tejun Heo 指出，随着 struct_ops 子系统（特别是 sched_ext 调度器扩展）对 BPF arena 的使用需求增加，外部组件需要一种安全的方式来获取 arena 的内核虚拟地址起始值（kern_vm_start）以及从 BPF 程序反向查找其关联的 arena map。为此，补丁引入了：

- `bpf_arena_map_kern_vm_start(struct bpf_map *map)`：通过 BPF map 指针直接返回对应 arena 的 `kern_vm_start`，用于在内核虚拟地址与用户地址间进行转换。sched_ext 的后续工作正是依赖这一转换来管理 arena 内存映射。
- `bpf_prog_arena(struct bpf_prog *prog)`：返回给定 BPF 程序引用的 arena 所对应的 `bpf_map` 指针，若程序未引用任何 arena 则返回 NULL。由于验证器强制每个程序最多关联一个 arena，该函数使得 struct_ops 使用者能够自动发现成员程序中的 arena，并安全地获取 map 引用。

这两个函数均被设计为对现有 `bpf_arena_get_kern_vm_start()` 的简单封装，保持接口一致且不破坏 arena 的内部封装。Kumar Kartikeya Dwivedi 提出了相关建议，补丁也体现了社区对增强 struct_ops 与 arena 互操作性的共识。这个改动是作为一个 8 补丁系列的一部分，旨在为后续的 sched_ext 功能铺路。

## 参与讨论人员
- Tejun Heo (tj@kernel.org) — 补丁作者，Linux 内核维护者。
- Emil Tsalapatis (emil@etsalapatis.com) — 审查者，提供 Reviewed-by 标签。

## 达成的结论
已达成初步共识。Emil Tsalapatis 对补丁进行了审查并明确给出 `Reviewed-by` 标签，未提出任何修改意见或技术异议，表明补丁在逻辑和实现上得到了认可。当前讨论未见争议。

## 下一步改进方向
- 补丁需继续等待其他核心 BPF 维护者（如 Alexei Starovoitov、Daniel Borkmann 等）的审查与最终 Ack。
- 作为 8 补丁系列中的第 5 个，整体功能依赖于前序补丁的合并，后续需确保整个系列通过测试并解决可能的依赖冲突。
- 针对 struct_ops 的后续 sched_ext 补丁将依赖这两个新函数，需确认它们能正确处理所有边界情况（如 NULL arena、多程序引用等）。

## 新增补丁
本邮件仅讨论 PATCH 5/8 的初版，未在本线程内发布新的补丁版本。补丁版本信息：**[PATCH 5/8]**，由 Tejun Heo 于 Wed, 20 May 2026 发布，包含 `include/linux/bpf.h` 和 `kernel/bpf/arena.c` 的改动。

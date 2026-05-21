# bpf: Recover arena kernel faults with scratch page

---

## 更新 - 2026-05-21 02:42 UTC

## 核心话题
本邮件讨论围绕一个 BPF arena 内存管理补丁系列（v2）展开，核心是使用“scratch page”机制在内核发生缺页故障（fault）时进行恢复，以增强 BPF arena 的健壮性。该系列共 8 个补丁，邮件中引用了补丁 2/8 的说明。补丁修改涉及 `arch/arm64/mm/fault.c` 和 `arch/x86/mm/fault.c`，表明此机制同时支持 ARM64 和 x86 架构。  
技术上，arena 是 BPF 中用于用户态与内核态共享大段连续虚拟内存的区域，当内核访问 arena 映射的地址发生保护故障或无效地址时，通过 scratch page（临时填充页）避免内核崩溃，从而允许程序安全地处理错误。此补丁的 v2 版本采纳了 David Hildenbrand 的建议，在 `apply_range_clear_cb()` 中使用 `ptep_get_and_clear()` 替代原来操作，确保页表条目操作的原子性及一致性。Alexei Starovoitov 评论说“前 5 个补丁看起来不错”，并提出是否应创建一个稳定分支，将这些补丁同时拉入 `bpf-next` 与 `sched-ext` 两棵开发树，以便他后续在此基础之上提交 “slab-over-arena” 的改进。这表明补丁不仅是简单的修复，还是为更复杂的 slab 分配器运行于 arena 内存之上铺路的依赖项，具有基础设施性质。涉及的架构缺页处理路径调整，显示出 BPF arena 的实现必须与具体 CPU 的内存管理细节协同，ARM64 部分同样重要。

## 参与讨论人员
- Alexei Starovoitov (alexei.starovoitov@gmail.com) — BPF 维护者  
- Tejun Heo (tj@kernel.org) — 补丁提交者，sched-ext 维护者  
- Kumar Kartikeya Dwivedi (memxor@gmail.com) — 补丁作者之一  
- David Hildenbrand (david@kernel.org) — 内核内存管理专家，提供了代码改进建议  

## 达成的结论
本次邮件中 Alexei 明确表示前 5 个补丁已通过他的评审（lgtm），并提议创建稳定分支以便多树共享。Tejun Heo 尚未直接回复，但结合上下文，此提议属于维护者间的常见协作方式，且未出现反对意见，可以认为在补丁质量接纳上已达成初步共识：v2 系列的前半部分可以合并，但需先建立稳定的 base 分支。关于后 3 个补丁未作评价，可能是后续讨论的内容。

## 下一步改进方向
- 创建一个包含前 5 个补丁的稳定分支，并确保该分支被同时拉入 `bpf-next` 和 `sched-ext` 树，避免重复提交。  
- Alexei 将基于该稳定分支提交 “slab-over-arena” 的后续补丁，需要完成开发与审核。  
- 剩余 3 个补丁需要进一步评审，可能涉及更多架构级测试与性能验证。  
- arm64 部分的具体实现需要确保在缺页处理路径上不会引入副作用，可能需要专门的 ARM64 平台测试。  

## 新增补丁
本次邮件讨论的是已发布的 v2 补丁系列，未在该线程中发布新的补丁版本。v2 与前一版本的区别明确记录为：“在 `apply_range_clear_cb()` 中使用 `ptep_get_and_clear()`（David 的建议）”。

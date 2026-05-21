# Fix __pkvm_init_vm error path

---

## 更新 - 2026-05-21 14:07 UTC

## 核心话题
该邮件讨论的是针对 ARM64 架构下 pKVM（protected KVM）中 `__pkvm_init_vm` 错误路径修复的补丁系列（v2）。Vincent Donnefort 提交了三个补丁，旨在解决 Sashiko 报告的潜在引用计数泄露问题：当 `insert_vm_table_entry` 失败时，已捐赠给 hypervisor 的页面可能未被正确释放，导致 page refcount 出现泄漏。第一个补丁在 `hyp_pool_init` 中主动初始化 `hyp_page` 的 order 字段，避免后续操作依赖未初始化的值；第二个补丁修复了 `__pkvm_init_vm` 的错误处理逻辑，确保在表项插入失败时能够正确地回滚和清理已分配的页面；第三个补丁为 `__pkvm_hyp_donate_host` 添加了“安全网”（fail-safe），防止该函数在捐赠主机的引用计数页面时出现隐形泄漏，即若捐赠过程中检测到页面仍被引用计数锁定，则明确拒绝操作而非忽略错误。整个系列涉及 `arch/arm64/kvm/hyp/` 下的 4 个文件，共修改 34 行，新增 34 行，删除 11 行。补丁 v2 相较 v1 的主要变化是在 `hyp_pool_init` 中“proactively”设置 `hyp_page` order 字段，体现防守性编程思路。Fuad Tabba 的回复仅指出补丁集封面信（cover letter）中“BLURB HERE”占位符未被替换为实际描述，属于格式上的小疏忽（nit）。技术层面没有进一步讨论，但核心意图明确：加固 pKVM 内存管理，保证在异常路径下不会丢失对 refcount 页面的跟踪，维护系统的内存一致性。此修复对运行保护型虚拟机的 ARM64 平台至关重要，因为一旦 refcount 泄漏，将导致物理内存无法回收，最终资源耗尽。

## 参与讨论人员
- Vincent Donnefort (Google) —— 补丁作者，负责修复 __pkvm_init_vm 错误路径
- Fuad Tabba (Google) —— 代码审查者，指出 cover letter 中 BLURB 未填充
- Sashiko —— 报告了 insert_vm_table_entry 失败时潜在的 refcount 泄漏（具体全名未在邮件中提及，应为同一团队或社区贡献者）

## 达成的结论
未就补丁本身达成实质性共识，仅发现一处文档排版问题：补丁集封面信未填写实际内容（仍然保留 “BLURB HERE” 占位符）。Fuad Tabba 以“nit: missing BLURB :)”方式提出轻微提醒，表明审查尚未深入技术逻辑，目前处于早期 review 阶段。后续可能等待补丁作者修正描述后继续评审，没有产生技术分歧。

## 下一步改进方向
- Vincent Donnefort 需完善补丁集封面信，用实质性内容替换 “BLURB HERE”，简要说明整个系列的目的、背景及改动总结，以方便评审者快速理解。
- 后续需要其他维护者（如 ARM64 pKVM 子系统负责人）进行详细代码审查，重点验证 `__pkvm_init_vm` 错误路径是否真正闭合了所有泄漏缺口，以及 `__pkvm_hyp_donate_host` 的 fail-safe 逻辑是否严格且无副作用。
- 可能需要补充测试用例，覆盖 `insert_vm_table_entry` 失败各种场景（如缺页分配失败、表项冲突等），确认 refcount 能正确归零或得到妥善处理。
- 如果审查通过，可能发布 v3 版本，包含封面信修复及有可能的技术调整；若无更多问题，本系列可被合入相关分支。

## 新增补丁
本次邮件未发布新版本补丁，仍为 v2 系列。作者在介绍中提及 v2 相比 v1 的变化是“Proactively init hyp_page order field in hyp_pool_init”，该变化已体现在 v2 提交中。Fuad Tabba 的回复仅提出格式建议，未催生 v3，因此尚未出现新补丁。

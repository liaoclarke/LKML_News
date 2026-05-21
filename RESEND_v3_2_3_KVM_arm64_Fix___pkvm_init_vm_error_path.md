# [RESEND v3 2/3] KVM: arm64: Fix __pkvm_init_vm error path

---

## 更新 - 2026-05-21 15:36 UTC

## 核心话题
该补丁修复了ARM64 pKVM（protected KVM）中`__pkvm_init_vm`函数的错误处理路径。在初始化受保护的虚拟机时，如果`insert_vm_table_entry`调用失败（一种不太可能发生的情况），原代码会释放主机捐赠给页全局目录（PGD）的内存。但由于此时第二阶段页表（stage-2）已经建立，虚拟机管理程序仍持有对这些页面的引用计数，导致引用计数泄漏。补丁通过引入一个新函数`kvm_guest_destroy_stage2()`来正确回滚第二阶段页表状态，进而解决该泄漏问题。技术细节上，该函数在获取guest组件的锁之后，调用`kvm_pgtable_stage2_destroy`销毁stage-2页表，并将`vm->kvm.arch.mmu.pgd_phys`置零，最后释放锁。这比之前仅回收PGD页面却不清除stage-2映射的做法更彻底，确保了引用计数的正确平衡。补丁的修复目标直接指向提交`256b4668cd89`（"KVM: arm64: Introduce separate hypercalls for pKVM VM reservation and initialization"）引入的不足，属于错误路径处理增强。

## 参与讨论人员
- Vincent Donnefort (vdonnefort@google.com) — 补丁作者，来自Google
- Sashiko (sashiko-bot@kernel.org) — 问题报告者（内核自动化测试机器人）
- Fuad Tabba (tabba@google.com) — 审核并测试了补丁（Reviewed-by、Tested-by），来自Google

## 达成的结论
该补丁已通过审核和测试（由Fuad Tabba提供Reviewed-by和Tested-by标签），作为v3补丁重新发送。没有出现反对意见或待解决的争议，表明已经达成共识，认为该修复是正确且必要的。此补丁属于稳定化改进，可并入主线的ARM64 KVM代码中。

## 下一步改进方向
该补丁状态为“RESEND v3”，表明之前可能未引起足够注意或被遗漏，现重新发送以寻求合入。下一步需要相关维护者（如Marc Zyngier或Catalin Marinas等ARM64 KVM维护者）将其纳入arm64或kvmarm树，最终推向主线。暂无明确的额外代码改动需求。

## 新增补丁
本线程中重新发送了v3版本的补丁，标题为“[RESEND v3 2/3] KVM: arm64: Fix __pkvm_init_vm error path”。与之前版本相比（未在片段中详细列出），v3主要变更可能是针对此错误路径修复，且已获得Reviewed和Tested标签。原补丁系列共三部分，此为第二部分，具体变更见邮件内嵌的diff内容（新增`kvm_guest_destroy_stage2`并在错误路径中调用）。

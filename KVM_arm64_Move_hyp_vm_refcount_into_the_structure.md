# KVM: arm64: Move hyp_vm refcount into the structure

---

## 更新 - 2026-05-20 16:26 UTC

## 核心话题
本补丁是 pKVM 相关系列（共 17 个补丁）中的第 13 个，旨在为后续使用 pKVM 堆分配器（`hyp_alloc()`）分配 `pkvm_hyp_vm` 结构做准备。在此之前，`hyp_vm` 的引用计数依赖于页面元数据（vmemmap），通过 `hyp_page_ref_inc()` 和 `hyp_page_ref_dec()` 操作与该结构体所在的物理页面绑定。然而，`hyp_alloc()` 的设计允许多个小对象共享同一个物理页面，因此每个 `hyp_vm` 对象不再独占一个物理页，基于页面的引用计数模型无法继续使用。

为此，补丁将引用计数整合到 `struct pkvm_hyp_vm` 内部，新增一个 `unsigned short refcount` 字段，并提供了两个内联辅助函数：`pkvm_hyp_vm_ref_inc()` 和 `pkvm_hyp_vm_ref_dec()`，分别对引用计数进行增加和减少，同时通过 `BUG_ON` 检查溢出（达到 `USHRT_MAX`）和下溢（计数为零时减少）。引用计数的主要使用者是在 vCPU 加载/卸载路径中：`pkvm_load_hyp_vcpu()` 获取 `hyp_vm` 引用，`pkvm_put_hyp_vcpu()` 释放引用。补丁将原 `hyp_page_ref_inc(hyp_virt_to_page(hyp_vm))` 替换为 `pkvm_hyp_vm_ref_inc(hyp_vm)`，相应的 `put` 操作也被替换（补丁片段末尾显示替换了 `hyp_page_ref_dec` 调用，但由于邮件截断未完全展示）。

该改动解耦了 VM 引用计数与底层物理页的生命周期管理，使得 `hyp_vm` 可以被灵活放置在共享页面中，为后续采用 `hyp_alloc()` 动态分配 VM 结构扫清障碍。同时，选择 `unsigned short` 类型的引用计数意味着最大引用值为 65535，这对于 pKVM 场景下 VM 被引用的次数（通常与 vCPU 数量相当）是足够的，且放在结构体内可以避免额外的内存访问，性能友好。

## 参与讨论人员
- Vincent Donnefort (Google)：补丁作者。

（该线程仅包含本封邮件，无其他参与者回复。）

## 达成的结论
由于邮件为单独提交的补丁，尚未收到回复或审查意见，因此未达成任何共识。补丁的技术方案和实现细节有待社区进一步讨论。

## 下一步改进方向
1. 等待 ARM64/KVM 维护者及其他开发者的审查，确认将引用计数移入结构体的设计是否合理，尤其是 `unsigned short` 类型的范围是否足够应对所有可能的引用场景。
2. 需要验证在并发条件下，对 `refcount` 的修改是否在持有合适的锁（如 `vm_table_lock`）时进行，以确保线程安全（从代码片段看，`inc/dec` 操作分别在 `pkvm_load_hyp_vcpu` 和 `pkvm_put_hyp_vcpu` 中的 `vm_table_lock` 临界区内，但后续调用也可能需要关注）。
3. 确保所有原先通过 `hyp_page_ref` 操作的地方都已正确替换为新的 `pkvm_hyp_vm_ref_*` 接口，避免遗留引用计数不一致的问题。
4. 可能需要补充对 `pkvm_hyp_vm` 结构体大小变化的影响分析，因为新增的 `refcount` 字段会轻微增加内存占用（2 字节），但在对象可共享页面后整体内存利用率会提高。

## 新增补丁
本邮件提交的是系列补丁的 v1 版本（即 PATCH 13/17）。由于邮件被截断，未显示新的版本号或后续更新。

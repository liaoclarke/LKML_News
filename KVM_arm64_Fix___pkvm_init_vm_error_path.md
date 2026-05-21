# KVM: arm64: Fix __pkvm_init_vm error path

---

## 更新 - 2026-05-21 14:07 UTC

## 核心话题
本次讨论围绕 KVM/ARM64 的 pKVM（protected KVM）子系统中的一个引用泄漏问题展开。  
在 `__pkvm_init_vm` 函数的错误处理路径中，如果 `insert_vm_table_entry` 调用失败，代码会释放宿主捐赠给 Stage-2 页全局目录（PGD）的内存，但由于此时 Stage-2 页表已经被设置好，Hypervisor 仍然持有对这些页面的引用计数，导致引用泄漏，内存无法被回收。  

Vincent Donnefort 指出该问题由提交 `256b4668cd89`（"KVM: arm64: Introduce separate hypercalls for pKVM VM reservation and initialization"）引入，并由自动化工具 Sashiko 报告。修复方案是新增一个 `kvm_guest_destroy_stage2()` 函数，该函数在 Guest 组件锁的保护下调用 `kvm_pgtable_stage2_destroy()` 销毁 Stage-2 页表，并清零 `pgd_phys` 字段，从而正确释放引用。在 `__pkvm_init_vm` 的错误回滚路径中调用该新函数即可解决泄漏问题。  

补丁还包含了必要的头文件声明和内部实现调整，使得 `reclaim_pgtable_pages` 等现有代码能与新函数共存。  

从代码片段可见，`kvm_guest_destroy_stage2` 的实现简洁且对称于已有的 `kvm_guest_prepare_stage2`，符合预期的资源管理模式。补丁虽针对一个“unlikely”的错误场景，但避免了潜在的内存泄漏，对系统长期稳定性有重要意义。

## 参与讨论人员
- Vincent Donnefort (Google) – 补丁作者  
- Fuad Tabba (Google) – 审核与测试人员  
- Sashiko <sashiko-bot@kernel.org> – 问题报告者（自动化工具，非人类参与者）

## 达成的结论
达成明确共识。  
Fuad Tabba 给出了 `Reviewed-by: Fuad Tabba <tabba@google.com>` 和 `Tested-by: Fuad Tabba <tabba@google.com>` 的标签，表明其对补丁的正确性和测试结果已确认，同意合入。邮件中没有出现任何反对意见或进一步讨论。

## 下一步改进方向
补丁已获得审核与测试标签，可直接由 ARM64 KVM 维护者合入主线。  
后续可能需要：
- 确认该补丁是否已包含在系列的其他部分（v2 系列为 2/3），若有依赖补丁需一并合入。
- 若未合入，可提交 pull request 或在补丁跟踪系统中进行最终合入动作。

## 新增补丁
- **v2**：由 Vincent Donnefort 发送的 `[PATCH v2 2/3] KVM: arm64: Fix __pkvm_init_vm error path`。相比最初的 v1（PATCH 1/2），补丁功能相同，但在系列中位置调整为 2/3，可能伴随其他补丁的重组或更新。该版本获得 Fuad Tabba 的 review 和 test 标签。

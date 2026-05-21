# KVM: arm64: Alloc pkvm_hyp_vm using pKVM heap allocator

---

## 更新 - 2026-05-20 16:26 UTC

## 核心话题
该补丁是 Vincent Donnefort 提交的 KVM/ARM64 pKVM 系列（共 17 个补丁）中的第 15 个，旨在将受保护虚拟机管理结构 `pkvm_hyp_vm` 的分配职责从主机（EL1）转移到 hypervisor（EL2），并利用新引入的 pKVM 堆分配器（`hyp_alloc()`）在 EL2 动态完成内存分配。具体技术背景和关键改动如下：

**原方案的问题**  
此前，主机端在创建 pKVM 虚拟机时，需要提前通过类似 `DEFINE(PKVM_HYP_VM_SIZE, sizeof(struct pkvm_hyp_vm))` 的宏计算出结构体大小，并在主机侧分配一整块连续物理内存，然后通过“捐赠内存”的形式交由 hypervisor 使用。该模式导致主机必须知晓 EL2 内部数据结构的细节，违反了 pKVM 隔离原则，也增加了主机与 hypervisor 间的耦合度，维护和扩展性较差。

**新方案的设计**  
补丁删除了 `hyp-constants.c` 中的 `PKVM_HYP_VM_SIZE` 定义，表明主机不再需要关心该结构体的大小。`__pkvm_init_vm()` 的接口发生本质变化：原先签名需要 `unsigned long vm_hva` 和 `unsigned long pgd_hva` 两个主机虚拟地址，用于定位主机侧预分配的内存；新接口简化为 `int __pkvm_init_vm(struct kvm *host_kvm, void *pgd)`，仅传入一个指向页全局目录的指针，而 VM 状态结构则由 hypervisor 内部使用 `hyp_alloc()` 自行分配。补丁中 `hyp-main.c` 的处理函数 `handle___pkvm_init_vm()` 被修改：不再通过主机传下来的地址直接转换使用，而是调用 `hyp_alloc()` 从 EL2 堆中分配 `pkvm_hyp_vm`，若分配失败则通过“补货请求”机制（top-up request）让主机补充堆内存。

**对安全性和灵活性的影响**  
将分配逻辑上移至 hypervisor，意味着 `pkvm_hyp_vm` 的完整生命周期完全由 pKVM 控制，主机无法直接观测或篡改其内存布局。同时，补丁使用 `pkvm_call_hyp_req()` 包装器调用 `__pkvm_init_vm`，该包装器能自动检测 hypervisor 是否因堆内存不足而无法完成分配，并向主机发起补货请求，主机提供新内存后重试，从而透明地管理 EL2 堆的扩容，增强了系统稳定性。这一改动也是整个系列后续推进 hypervisor 独立内存管理的关键步骤。

## 参与讨论人员
- Vincent Donnefort <vdonnefort@google.com>（来自 Google）

该邮件为单一补丁提交，线程中暂无其他回复或讨论者。

## 达成的结论
由于仅有补丁提交动作，无后续审查、建议或反驳意见，因此该轮讨论尚未形成任何共识或结论。补丁等待社区（尤其是 KVM/ARM 维护者）的 review 和反馈。

## 下一步改进方向
1. 需要社区对补丁进行审查，重点关注：  
   - `hyp_alloc()` 在 VM 初始化早期阶段的可用性（堆是否已就绪）；  
   - `pkvm_call_hyp_req()` 的重试逻辑在分配失败时是否可能引入死锁或反复补货问题；  
   - 移除主机侧预分配后，对原有错误路径和资源回收的影响。  
2. 建议补充或加强测试，尤其是堆耗尽场景下补货机制的触发与恢复流程，以及并发创建多个 pKVM 虚拟机时的压力测试。  
3. 需结合补丁系列的前后依赖（如堆分配器本身的实现补丁）进行整体验证，确保接口变更与其余 16 个补丁没有遗漏的适配点（例如任何仍然引用 `PKVM_HYP_VM_SIZE` 或 `vm_hva` 参数的代码路径）。  
4. 未来可能需要提供文档或注释，说明为何将 `pkvm_hyp_vm` 交由 hypervisor 分配能带来安全优势，帮助 review 者理解改动意图。

## 新增补丁
本线程中出现的新补丁版本即为当前提交的 **v1**（补丁 15/17），尚未有基于 discussion 的更新版本。其变更摘要为：
- 删除 `PKVM_HYP_VM_SIZE` 常量，移除主机对 VM 结构大小的感知。  
- 简化 `__pkvm_init_vm` 参数，仅保留 `host_kvm` 和 `pgd`。  
- 在 `handle___pkvm_init_vm` 中使用 `hyp_alloc()` 动态分配 `pkvm_hyp_vm`，并通过 `pkvm_call_hyp_req` 集成堆补货重试机制。

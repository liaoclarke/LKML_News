# dma: swiotlb: free dynamic pools from process context

---

## 更新 - 2026-05-22 09:58 UTC

## 核心话题
该邮件讨论的是 ARM64 架构下 SWIOTLB 动态内存池释放路径的上下文问题。  
补丁作者指出，`swiotlb_dyn_free()` 函数在从 RCU 保护链表中移除动态 SWIOTLB Pool 后被调用，内部会调用 `swiotlb_free_tlb()`。对于需要恢复加密状态的“非加密池”，`swiotlb_free_tlb()` 会在释放页面之前调用 `set_memory_encrypted()`。然而，RCU 回调（原 `rcu_head` 的回调函数）运行在原子上下文中，而 `set_memory_encrypted()` 并非在所有架构上都保证原子安全，例如在执行过程中可能需要分配页表或获取可睡眠的锁，这在原子上下文中是不允许的。这一限制在 ARM64 等架构上可能导致问题。  

为了解决此矛盾，补丁将原 `struct rcu_head rcu` 替换为 `struct rcu_work dyn_free`，并将相应的释放逻辑改为使用 `queue_rcu_work()` 进行调度。`queue_rcu_work()` 在内核中的语义是：在经历了完整的 RCU 宽限期（grace period）后，通过工作队列（workqueue）在进程上下文中执行给定的工作项。这样既保证在释放池资源之前，所有已发布的池引用都已过 RCU 保护期，又确保实际的池销毁操作（包括 `set_memory_encrypted()`）在允许睡眠的进程上下文中执行，避免了原子上下文非法调度的风险。  

补丁同样考虑了“临时池”（transient pool）的错误路径，因为该路径也可能从原子的 DMA 映射上下文中进入，因此也统一使用了相同的 RCU 工作项释放机制。这对动态 SWIOTLB（`CONFIG_SWIOTLB_DYNAMIC`）配置是必需的变更，属于该系列补丁中第 17 号补丁。  

从补丁内容看，主要的数据结构修改是将 `io_tlb_pool` 中的 `struct rcu_head rcu` 改为 `struct rcu_work dyn_free`，并在实现中将原本直接通过 `call_rcu` 调度的回调绕道 `queue_rcu_work`。这种改动既优雅地维持了 RCU 保护，又解决了原子上下文限制，是架构无关的正确增强。

## 参与讨论人员
- Aneesh Kumar K.V (Arm) <aneesh.kumar@kernel.org>（补丁提交者，Arm 公司）

由于该邮件是单独的补丁提交，线程中未出现其他评审者或评论者的回复，因此参与讨论的只有提交者本人。

## 达成的结论
该邮件是一个独立的补丁提交，属于 `[PATCH v5 17/20]` 系列的一部分，未在邮件中看到任何回复、讨论或评审意见。因此，目前尚未达成任何共识或结论，补丁仍处于待审查状态。

## 下一步改进方向
- 该补丁需要获得内核 DMA 子系统及 ARM64 维护者的评审和测试，特别是确认在支持动态 SWIOTLB 且使用了加密内存池的平台上，释放路径确实不会因原子上下文导致死锁或非法调度；  
- 需要验证 `queue_rcu_work()` 的延迟与原有 `call_rcu()` 相比是否在可接受范围内，不会显著增加内存回收延迟；  
- 系列补丁整体需要完成剩余部分的提交、审查与合并流程，当前补丁可能依赖前序补丁；  
- 如果评审提出修改意见，可能需要发布新版本。

## 新增补丁
本邮件本身就是 `v5` 版本的补丁提交，为系列 `[PATCH v5 00/20]` 中的第 17 号补丁。该邮件内没有发布更新的补丁版本（如 v6），因此目前只有该 v5 版本的补丁。

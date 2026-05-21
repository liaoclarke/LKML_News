# KVM: arm64: Add a shrinker for pKVM

---

## 更新 - 2026-05-20 16:26 UTC

## 核心话题
本补丁旨在为 ARM64 架构下的 pKVM（protected KVM，受保护的内核虚拟机）引入一个 shrinker 机制，将 Hypervisor（hyp）端内存分配器与宿主机的内存管理子系统（MM）集成。主要动机是当宿主机面临内存压力时，能够自动回收位于 Hypervisor 堆分配器中的未使用内存，从而避免宿主 OOM 或性能劣化，同时不影响受保护虚拟机的安全属性。

技术关键点如下：
- **shrinker 操作接口**：补丁定义了两个标准的内存回收回调函数 `pkvm_shrinker_count` 和 `pkvm_shrinker_scan`。其中 `count` 通过调用 `pkvm_hyp_reclaimable(PKVM_TOPUP_HYP_ALLOC)` 获取当前可回收的 hyp 页数，若无则返回 `SHRINK_EMPTY`；`scan` 则实际执行回收，调用 `pkvm_hyp_reclaim` 并传递 `sc->nr_to_scan` 作为期望回收的数量，函数返回实际回收的页数。正如邮件原文所示：
  > `return pkvm_hyp_reclaimable(PKVM_TOPUP_HYP_ALLOC) ?: SHRINK_EMPTY;`
  > `return pkvm_hyp_reclaim(PKVM_TOPUP_HYP_ALLOC, sc->nr_to_scan);`

- **shrinker 注册时机**：shrinker 在 pKVM 初始化过程中被创建并注册。具体在 `init_hyp_mode()` 函数中，当 `is_protected_kvm_enabled()` 为真，且所有 hyp 内存保护初始化完成后，调用 `shrinker_alloc(0, "pkvm")` 分配一个 shrinker 结构，设置其操作对象并注册到内核的 shrinker 框架中。如果分配失败，则打印错误信息，但不会导致整个 pKVM 初始化失败，这种做法保证了 pKVM 核心功能的可用性，仅仅是内存自动回收功能缺失。

- **与现有 pKVM 内存管理的对接**：前缀为 `pkvm_hyp_*` 的函数应是之前补丁在该系列中引入的 hyp 内存回收接口，此处通过 shrinker 将它们暴露给宿主机 MM。`PKVM_TOPUP_HYP_ALLOC` 常量可能指代某种回收策略或内存池标识，暗示 hypervisor 堆分配器支持按需 top-up 回收。

- **代码位置变更**：补丁还在 `init_hyp_mode()` 中添加了 ARM64 指针认证（Pointer Authentication）相关的初始化逻辑（`pkvm_hyp_init_ptrauth()`），但这部分属于上下文变动，核心仍是 shrinker 的集成。

总体而言，该补丁是 pKVM 系列中实现内存弹性的关键一环，通过向宿主机 MM 注册 shrinker，使得 hyp 内存不再是固定预留，而是在宿主机需要时能够动态回收，平衡了安全隔离与资源利用率。

## 参与讨论人员
- Vincent Donnefort <vdonnefort@google.com> （Google）

## 达成的结论
本邮件仅为单封补丁提交，属于系列 [PATCH 11/17] 的一部分，尚未见到任何回复或评论，因此并未达成任何明确结论。没有可见的 Acked-by 或 Reviewed-by 标签，也没有人提出异议或修改建议。

## 下一步改进方向
由于缺乏社区反馈，可能的后续改进方向包括：
- 由 ARM64 KVM 维护人员审核该 shrinker 实现的安全性与正确性，尤其是 `pkvm_hyp_reclaim` 在 hyp 上下文中的并发控制和与 hyp 内存分配器的互操作性。
- 讨论 shrinker 注册失败是否应该作为致命错误（当前仅打印错误但继续引导）。若内存回收对系统稳定性至关重要，可能需要将失败视为初始化失败。
- 测试在宿主机内存压力下 shrinker 的行为，验证回收操作是否真的无害于受保护虚拟机，以及是否能够正确释放物理内存并归还给宿主机伙伴系统。
- 检查是否需要为 non-protected KVM 也引入类似的 hyp 内存回收机制，抽象出通用 shrinker 逻辑。
- 审核整个系列补丁中其他部分是否与本 shrinker 配合得当，例如 `PKVM_TOPUP_HYP_ALLOC` 的定义与使用。

## 新增补丁
本邮件中未发布新的补丁版本，仍为系列中的 v1 版本（PATCH 11/17）。无后续版本或变更记录。

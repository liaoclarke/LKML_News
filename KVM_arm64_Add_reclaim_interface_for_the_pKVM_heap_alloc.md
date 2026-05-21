# KVM: arm64: Add reclaim interface for the pKVM heap alloc

---

## 更新 - 2026-05-20 16:26 UTC

## 核心话题
本补丁（PATCH 09/17）针对 ARM64 pKVM（protected KVM）的内存管理，为 hyp 堆分配器引入一套可供主机（host）主动回收已捐赠内存的接口。在 pKVM 架构下，主机将内存捐赠给 hypervisor 以用于访客页表、hypervisor 自身的动态分配等，但此前缺乏灵活的“反向”回收机制。补丁明确提出：“Introduce a host interface to reclaim donated memory from the pKVM heap allocator back to the host.” 其核心诉求是为将来实现 pKVM 的 shrinker 提供基础，使得在主机内存压力增大时，能够将 hypervisor 中闲置的捐赠内存归还给主机，从而平衡安全隔离与系统整体内存需求。

技术实现上，补丁在 ARM64 的 SMCCC 调用枚举中新增了两个函数号：`__KVM_HOST_SMCCC_FUNC___pkvm_hyp_reclaim` 和 `__KVM_HOST_SMCCC_FUNC___pkvm_hyp_reclaimable`，并在头文件 `kvm_pkvm.h` 中声明了两个主机侧辅助函数：
- `pkvm_hyp_reclaimable(enum pkvm_topup_id id)`：查询对应 hyp 池中当前可回收的内存数量（例如空闲页面）。
- `pkvm_hyp_reclaim(enum pkvm_topup_id id, unsigned long target)`：实际从 hyp 堆回收指定数量的内存，将其页面归还给主机。

处理函数 `handle___pkvm_hyp_reclaim()` 的片段显示，它通过 `DECLARE_REG` 获取传入的池 ID 和目标回收量，并初始化一个 `struct kvm_hyp_memcache host_mc`。执行回收操作后，通过 `cpu_reg(host_ctxt, …) = host_mc.nr_pages` 将实际回收的页面数返回给主机调用者，这与同系列中 top‑up 接口的返回值模式一致。可以推断，底层依赖 hyp 页分配器内部的回收能力，以指定池的空闲页面或可释放的暂存内存作为回收来源。

这一接口的引入让 pKVM 内存管理从单向捐赠走向双向流动，是后续实现基于内存压力的自动收缩（shrinker）的关键前置工作。它为 pKVM 环境下的内存超量使用、容器化部署等场景提供了更精细的控制手段，同时也需要谨慎处理安全性：回收操作必须保证只针对主机原本捐赠且未被 hypervisor 固化的页面，以防破坏隔离边界。当前补丁仅提供基础原语，具体收缩策略将在后续补丁中展开。

## 参与讨论人员
- Vincent Donnefort (Google) — 补丁作者及发送人

（本线程仅包含此封补丁邮件，无其他回复或讨论者）

## 达成的结论
尚未达成任何结论。该补丁为系列的一部分，正等待社区维护者和相关开发者的审查与反馈。由于是单封提交，没有出现反对意见或采纳共识。

## 下一步改进方向
1. **等待社区审查**：需要 ARM64 KVM/pKVM 维护者（如 Marc Zyngier、Will Deacon 等）和相关开发者审查代码的正确性，特别是 Hyp 模式下的内存回收安全性，防止将仍在使用的关键页面回交给主机。
2. **完善代码细节**：补丁邮件内容被截断，可能存在未展示的错误处理或边界情况，后续版本需补充完整逻辑。
3. **与 shrinker 集成**：需配合后续补丁（预计本系列中的后续 patch）实际注册内核 shrinker，调用 `pkvm_hyp_reclaimable()` 和 `pkvm_hyp_reclaim()`，并测试在各种内存压力下的行为。
4. **测试**：在 pKVM 环境中验证回收操作不会引发 hyp 异常，并确认回收后的页面能够被主机正常重新分配使用。
5. **文档**：可能需要更新 Documentation/virt/kvm/arm/pkvm.rst 或相关文档，说明回收接口的用法和限制。

## 新增补丁
本邮件中包含以下新增补丁（为系列补丁之一）：
- **[PATCH 09/17] KVM: arm64: Add reclaim interface for the pKVM heap alloc**
  - 版本：v1（系列为 17 个补丁，此为第 9 个）
  - 变更：新引入 `pkvm_hyp_reclaimable()` 和 `pkvm_hyp_reclaim()` 主机接口，并增加对应的 Hyp SMCCC 处理路径，从 hyp 堆分配器回收捐赠内存回主机。

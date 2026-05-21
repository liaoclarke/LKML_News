# KVM: arm64: Alloc pkvm_hyp_vcpu using pKVM heap allocator

---

## 更新 - 2026-05-20 16:26 UTC

## 核心话题
该邮件是 Vincent Donnefort (Google) 提交的 ARM64 KVM pKVM (protected KVM) 系列补丁的第 16 个补丁，主题为“KVM: arm64: 使用 pKVM 堆分配器分配 pkvm_hyp_vcpu”。该补丁的目标是将 hypervisor 端 vCPU 状态结构体 `pkvm_hyp_vcpu` 的分配职责从主机（host）转移到 hypervisor（EL2），并利用新引入的 pKVM 堆分配器 (`hyp_alloc()`) 进行动态内存管理。

在之前的实现中，主机内核在创建虚拟机时需要计算 `pkvm_hyp_vcpu` 结构体的大小，为其分配物理内存，并将这些内存“捐赠”给 hypervisor。主机端代码为此维护了一个 `teardown_mc` 内存缓存 (`struct kvm_hyp_memcache`) 用于回收该结构体的内存，并且在编译期通过 `PKVM_HYP_VCPU_SIZE` 常量来获取结构体大小（在 `hyp-constants.c` 中定义）。这种设计将内存管理的复杂性留在了主机侧，不仅增加了主机与 hypervisor 之间的耦合，也使得 hypervisor 缺乏弹性——一旦内存被捐赠，其生命周期完全由主机控制。

新设计中，补丁移除了主机端的 `teardown_mc` 字段（`kvm_protected_vm` 结构体中），并删除了 `STRUCT_HYP_PAGE_SIZE` 之外不再需要的 `PKVM_HYP_VCPU_SIZE` 常量定义。取而代之的是，hypervisor 在运行时通过 `hyp_alloc()` 直接从 pKVM 堆中分配 `pkvm_hyp_vcpu` 结构体。为了处理堆内存不足的情况，补丁使用 `pkvm_call_hyp_req()` 封装了 `__pkvm_create_hyp_vcpu` 的调用，该封装函数能够在分配失败时自动触发“top-up”（补充）请求，让主机向 hypervisor 堆补充内存，从而透明地完成分配。

这一转变的核心技术动机是：
1. **隔离与简化**：将内存分配逻辑完全移入 EL2，使主机代码更简单，减少了 hypervisor 与主机之间的接口，符合 pKVM 保护虚拟机设计理念——最小化主机对保护虚拟机的控制和访问。
2. **动态管理**：利用 pKVM 堆分配器使得 hypervisor 可以自行决定何时申请内存，而不是在 VM 创建时一次性大量捐赠，增强了内存使用的灵活性和可扩展性。
3. **一致性**：与系列中其他补丁（如为 VM 结构体、Stage-2 页表等使用堆分配器）保持一致，逐步将所有 hypervisor 内部数据结构迁移到统一的堆分配框架下。
4. **移除编译期依赖**：消除主机端通过 `PKVM_HYP_VCPU_SIZE` 获取结构体大小的需求，因为 hypervisor 完全掌控分配，主机无需知晓该结构的大小，降低了内核升级或配置变化时主机与 hypervisor 数据结构不匹配的风险。

补丁的 diff 显示了对 `arch/arm64/include/asm/kvm_host.h`、`arch/arm64/kvm/hyp/hyp-constants.c` 和 `arch/arm64/kvm/hyp/include/nvhe/pkvm.h` 等文件的修改，但邮件内容被截断，未完整展示 `__pkvm_init_vcpu` 等函数的接口变化细节。不过可以推断，原来的 `__pkvm_init_vcpu` 接受一个由主机捐赠的内存地址，而现在将改为由 hypervisor 内部分配。

## 参与讨论人员
- Vincent Donnefort (Google)：补丁提交者。

## 达成的结论
本邮件仅包含补丁提交，没有后续回复讨论，因此未达成任何共识或结论。该补丁尚处于待审查状态。

## 下一步改进方向
- 补丁需要经过内核社区的审查（review），特别是 ARM64 KVM 维护者（如 Marc Zyngier、Oliver Upton 等）及 pKVM 相关开发者的反馈。
- 可能需要补充更详细的提交说明，解释 transition 过程中对主机 `teardown_mc` 移除的并发安全性或内存回收路径的处理。
- 需要与同一系列中其他补丁（如堆分配器引入、VM 结构体的堆分配改造等）进行集成测试，确保在内存压力、VM 创建/销毁、vCPU 热插拔等场景下无内存泄漏或分配失败。
- 如果审查中提出修改意见，可能需要发送 v2 版本。

## 新增补丁
本线程中未出现新版本补丁，仅有 PATCH 16/17 初始版本。

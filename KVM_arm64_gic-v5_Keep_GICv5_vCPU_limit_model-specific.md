# KVM: arm64: gic-v5: Keep GICv5 vCPU limit model-specific

---

## 更新 - 2026-05-21 14:53 UTC

## 核心话题
该补丁讨论的是 ARM64 KVM 虚拟化中 GICv5 的 vCPU 上限管理问题。在支持 FEAT_GCIE_LEGACY 特性的 GICv5 主机上，系统可以同时向虚拟机暴露原生 vGICv5 设备或传统的 vGICv3 设备。这两种中断控制器模型对最大 vCPU 数量的限制并不相同：vGICv5 的上限取决于硬件 IRS（Interrupt Routing Support）的 VPE（Virtual PE）容量，这是一个可能小于固定值的动态探测结果；而 vGICv3 的上限则是 KVM 中固定的 VGIC_V3_MAX_CPUS（通常为 512），不应受 GICv5 硬件容量限制的影响。

补丁指出，现有代码在创建 vGICv5 设备时将 VM 的 max_vcpus 设置为 `min(VGIC_V5_MAX_CPUS, kvm_vgic_global_state.max_gic_vcpus)`，而 max_gic_vcpus 是从 IRS VPE 容量中获取的通用值。这会导致两个问题：一是将 GICv5 的硬件限制错误地用于所有 GIC 模型的默认思路；二是未明确区分不同模型的独立上限。作者强调：“A GICv5 host with FEAT_GCIE_LEGACY can expose both a native vGICv5 or a vGICv3 device. These models do not necessarily have the same vCPU limit: the native GICv5 limit is probed from the IRS VPE capacity, while the GICv3 limit remains the fixed KVM vGICv3 limit.” 因此，补丁的核心改动是将 GICv5 特有的 vCPU 上限保存在 `kvm_vgic_global_state.max_gicv5_vcpus` 中，并在创建 vGICv5 设备时直接使用该值，不再与通用的 max_gic_vcpus 取最小值。同时，对于 vGICv2 和 vGICv3，创建时依然使用各自的固定上限 `VGIC_V2_MAX_CPUS` 和 `VGIC_V3_MAX_CPUS`。补丁还提到，在 VGIC 设备创建之前，通过 `KVM_CAP_MAX_VCPUS` 向用户空间暴露的仍然是所有可选模型中最大的那个上限（即 vGICv3 的 512 与 GICv5 的动态上限之间的较大值），这样用户空间在尚未选择 GIC 型号时可以看到最大的理论 vCPU 数量，而一旦通过 `kvm_vgic_create()` 选定了具体模型，VM 的 max_vcpus 就会被钳制到该模型的实际上限，保证一致性。

具体的代码变更包括：在 `vgic-init.c` 的 `kvm_vgic_create()` 中，将原来针对 VGIC_V5 的 `k

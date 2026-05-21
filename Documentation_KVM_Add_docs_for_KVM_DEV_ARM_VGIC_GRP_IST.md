# Documentation: KVM: Add docs for KVM_DEV_ARM_VGIC_GRP_IST

---

## 更新 - 2026-05-21 15:02 UTC

## 核心话题
此邮件是 ARM64 架构 KVM 虚拟化中 VGICv5 设备模型的一个补丁（v2 系列的第 38/39），旨在为用户空间提供 IST（Interrupt State Table，中断状态表）的保存与恢复接口文档。补丁在 `Documentation/virt/kvm/devices/arm-vgic-v5.rst` 中新增了 `KVM_DEV_ARM_VGIC_GRP_IST` 组的描述，使得用户空间（如 QEMU）能够通过 VGIC 设备属性的 get/set 操作迁移 GICv5 中断控制器的状态。

关键技术点：
- **IST 背景**：VGICv5 引入了 IRS（Interrupt Routing Subsystem）以及与之绑定的 IST，用于存储 SPI 和 LPI 的中断状态。IST 分为 SPI IST（无 guest 可寻址的内存，状态由 KVM 内部管理）和 LPI IST（由 guest 通过 `IRS_IST_CFGR` 和 `IRS_IST_BASER` 寄存器配置的线性虚拟地址空间提供）。
- **接口语义**：`kvm_device_attr.attr` 必须为 0。get 操作触发 IST 保存：KVM 先要求 IRS 将运行中的中断状态写回 IST 并进入静止状态（quiesce），随后将 SPI IST 状态和 guest 内存中的 LPI IST 一同拷贝给用户空间。set 操作则用于恢复 IST 状态，必须在 VM 尚未运行且 IRS 状态、guest 内存均已恢复之后执行。若 guest 未启用 LPI IST，则对应部分的保存/恢复会被跳过。
- **错误条件**：如果 VGIC 未初始化或 VCPU 正在运行，操作会返回 `-EBUSY`；数据大小需正确，寄存器访问需按文档约定的对齐要求（如 64 位对齐）。
- **截断情况**：邮件最后显示“The SPI IST has no guest-owned backing memory, s...”，表明补丁粘贴不完整，完整描述可能还涉及 SPI IST 内存格式、大小计算等细节。但由于仅此一封邮件，无法得知后续讨论。

该文档补丁是为了配套 KVM 对 ARM GICv5 IST 保存/恢复的内核支持，使得完整 VM 迁移成为可能，是 VGICv5 虚拟化功能的重要组成部分。

## 参与讨论人员
- Sascha Bischoff (Arm) — 补丁作者与提交者

## 达成的结论
此邮件仅为一个独立的补丁提交，并非讨论结束后的总结帖，因此**未达成任何讨论结论**。提交目的是向社区提供文档供审阅。

## 下一步改进方向
- 补丁内容因邮件截断而不完整，需提交**完整版本的文档补丁**，补充 SPI IST 存储布局等缺失说明。
- 等待社区维护者（如 Marc Zyngier 等 KVM/arm64 维护者）审阅，确保接口语义与内核实现一致。
- 可能需要配合整个 v2 系列补丁的测试，验证文档描述与实际 KVM 行为吻合。
- 如果该接口是 VGICv5 新增功能，需确认与现有 VGICv3/v4 用户空间迁移流程的兼容性和扩展方式。

## 新增补丁
- `[PATCH v2 38/39]` — 这是 v2 补丁系列中的新增文档补丁，首次在这个位置引入 `KVM_DEV_ARM_VGIC_GRP_IST` 文档。相比于 v1（如果有），本版本可能根据前期反馈调整了描述或属性定义，但邮件中未体现版本间的具体变化。

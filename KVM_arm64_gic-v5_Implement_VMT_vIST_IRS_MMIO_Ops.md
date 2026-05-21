# KVM: arm64: gic-v5: Implement VMT/vIST IRS MMIO Ops

---

## 更新 - 2026-05-21 14:52 UTC

## 核心话题
本补丁是 Linux KVM ARM64 虚拟化支持未来 GICv5 中断控制器系列的第 11 个补丁（v2）。GICv5 为虚拟机监视器引入了更严格的 VMT（Virtual Machine Table，虚拟管理表）和 vIST（虚拟中断服务表）管理规则：一旦相关表被标记为有效（valid），硬件可能缓存其中的某些内容，因此宿主不能直接通过内存写操作修改部分字段（例如 Valid 位），而必须通过 IRS（Interrupt Redistribution Service，中断重分发服务）的 MMIO 接口，以特定的“操作命令”来变更有效性，从而保证硬件中不残留过时状态。

补丁说明明确指出：“GICv5 has rules about which fields of a VMTE (or L1 VMT) may be directly written by the host once the table is valid.” 因此，宿主负责填充 VMTE 的内容，但不能直接写入 Valid 位；VMT 和 IST 的有效化必须由宿主通过 IRS MMIO 操作触发。这项工作的核心就是为 KVM 添加对以下 vcpu_affinity 类 IRS 命令的支持：
- VMT_L2_MAP —— 让第二级 VM 表生效（支持动态分配 L2 表）；
- VMTE_MAKE_VALID / VMTE_MAKE_INVALID —— 使单个 VM 表项（即 VM）有效或无效；
- SPI_VIST_MAKE_VALID —— 使 SPI 的 IST 有效；
- LPI_VIST_MAKE_VALID / LPI_VIST_MAKE_INVALID —— 使 LPI 的 IST 有效或无效。

其中 SPI_VIST_MAKE_INVALID 被刻意缺失，补丁特别注明“the lack of SPI_VIST_MAKE_INVALID is intentional”，暗示硬件或架构限制不允许或现阶段不需要该操作。

补丁还涉及 VMT 的初始化和探针流程：成功探测到 GICv5 时会分配 VMT，并通过 IRS MMIO 将其标记为有效。说明强调：“Treat failures while allocating or assigning the VMT as hard GICv5 probe failures. … and falling back to the legacy path would leave the host without a valid GICv5 VM table setup.” 也就是说，若此阶段失败，整个 GICv5 支持被视为无法继续，不会回退到旧版路径，因为 IRS VM 表状态是 vGICv5 工作的前提。后期失败只有在已成功清除 IRS VMT 状态后才能安全回退。

实现上，修改涉及 `arch/arm64/kvm/vgic/vgic-v5-tables.c/h` 和 `vgic-v5.c`，加入了 58 行新增与 23 行删除等大量改动，为 KVM 虚拟中断子系统提供符合 GICv5 规范的 VMT 和 vIST 生命周期管理基础。

## 参与讨论人员
- Sascha Bischoff (Arm)

## 达成的结论
本邮件为补丁提交，并非讨论邮件，无其他参与者回复，因此未形成任何技术结论或共识。补丁等待社区审查与反馈。

## 下一步改进方向
- 等待 ARM64 KVM 维护者及社区对 GICv5 整体方案和本补丁实现细节的审查，关注 IRS 命令语义是否与架构规范完全一致。
- 对动态 L2 表分配及各种有效/无效转换的并发安全性和异常路径进行全面测试。
- 明确 SPI_VIST_MAKE_INVALID 为何刻意缺失，如果有必要，后续通过独立补丁补充相关操作。
- 确保在探针失败回退时，IRS 状态能被正确清除，避免留下部分配置导致硬件行为异常。
- 考虑是否需要在文档或代码注释中进一步澄清 VMTE 字段的直接写入限制与 IRS 操作之间的边界。

## 新增补丁
无。本邮件为 `[PATCH v2 11/39]`，且在该线程中未见更新版本。

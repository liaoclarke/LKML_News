# KVM: arm64: gic-v5: Implement save/restore mechanisms for ISTs

---

## 更新 - 2026-05-21 15:01 UTC

## 核心话题
本邮件是补丁“[PATCH v2 35/39] KVM: arm64: gic-v5: Implement save/restore mechanisms for ISTs”的提交说明，集中讨论了在 GICv5（ARM 通用中断控制器第五代）虚拟化场景下，如何实现在虚拟机（VM）迁移时对中断服务表（Interrupt Service Tables, ISTs）进行保存与恢复。GICv5 支持两类 IST：SPI IST 和 LPI IST。

- **SPI IST** 由 hypervisor 分配，因为 Guest 假定 SPI 状态内存由硬件分配。由于 Guest 没有为此分配内存，因此需要 VMM 提供一个足够大的内存缓冲区来保存/恢复 SPI IST（每个 SPI 占 32 位）。说明中提到：“As there is no guest-allocated memory for the SPI IST, the state of this must be saved by the VMM. Therefore, the VMM must provide a memory buffer large enough to store/restore the SPI IST (32-bits per SPI).”

- **LPI IST** 由 Guest 在希望使用 LPI 时分配，但 KVM 会为其创建一个影子拷贝，因此硬件实际使用的是 hypervisor 分配的表，而非 Guest 内存直接。保存时，每个 IST 条目被写回 Guest 内存（跳过元数据区域），恢复时则从 Guest 内存读回。补丁指出：“The LPI IST, if present, is stored into guest memory as the guest has already allocated storage under the assumption that it would be used by the GIC. Each IST Entry is written back to guest memory (skipping metadata sections) on a save, or restored from guest memory on a restore.”

保存流程中，VM 首先通过 `IRS_SAVE_VMR` 被静默（quiesced），以确保硬件已将所有中断状态写回 IST。之后检查 `IRS_SAVE_VM_STATUSR` 状态寄存器，如果发现 Guest 在保存期间脱离静默状态，则向上层 VMM 返回错误，以便重试保存操作。恢复流程则是先将 VM 标记为无效（防止其在表有效时写入），恢复 SPI 和 LPI IST（如需要），并清除 IST 中的 pending 状态。最后使 VM 重新有效，并通过 GIC 的 `VDPEND` 系统指令将之前记录的有效中断重新置为 pending。相关描述：“On restore, the VM is first made invalid … and then the SPI and LPI ISTs are restored … before making the VM valid again. As part of restoring the ISTs, any pending interrupts are tracked, and IST pending state is cleared. Once the VM is made valid, these valid interrupts are made pending again via the GIC VDPEND system instruction.”

这个补丁属于一个大型系列（v2 的第 35/39），其技术动机是为 VMM（如 QEMU）提供 GICv5 虚拟机的完整状态保存/恢复能力，从而支持热迁移。核心挑战在于协调硬件、hypervisor 及 Guest 对中断表的所有权，确保在迁移瞬间中断状态的准确性和一致性。

## 参与讨论人员
- Sascha Bischoff (Arm)

## 达成的结论
该邮件仅为补丁提交，线程中没有其他人的回复，因此未形成任何讨论或结论。

## 下一步改进方向
由于本邮件只是补丁系列的一部分，且没有后续评审反馈，下一步需要等待社区（尤其是 KVM/arm64 维护者）的审查。可能的改进方向包括：
- 代码审查后修正潜在的错误或风格问题；
- 补充更详细的文档说明 IRS_SAVE_VMR 等硬件指令的语义和约束；
- 测试验证各种边界条件，例如 Guest 在保存期间产生新中断的重试机制；
- 考虑与其他 GICv5 补丁的依赖性和交互。

## 新增补丁
本邮件即为 v2 系列的第 35 个补丁，未在后续回复中发布新的修订版本。

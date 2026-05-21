# iommu/arm-smmu-v3: Do not enable EVTQ/PRIQ interrupts in kdump kernel

---

## 更新 - 2026-05-20 10:03 UTC

## 核心话题
该补丁是 Linux 内核 arm-smmu-v3 驱动针对 kdump 场景的一个修复。在 kdump 内核启动时，前一个已崩溃内核的上下文描述符(CD)和页表可能已经损坏，这会引发以下问题：
1. **事件队列(EVTQ)中断洪水**：损坏的页表和 CD 可能导致大量地址转换错误，EVTQ 会产生非正常的中断风暴；
2. **PRI 页请求无法处理**：由于 kdump 内核并不掌管原本的 IOMMU 页表，无法正确处理 PRI 页请求，强行启用 PRIQ 中断只会导致无效甚至危险的行为。

因此补丁的动机是：在检测到当前运行在 kdump 内核时，**彻底跳过 EVTQ 和 PRIQ 中断的初始化和处理函数注册**，以避免中断风暴和无效处理。邮件中明确指出：
> “In kdump cases, the crashed kernel's CDs and page tables can be corrupted, which could trigger event spamming. Also, we cannot serve page requests.”

技术实现上，补丁修改了 `arm_smmu_setup_unique_irqs` 和 `arm_smmu_combined_irq_handler` 两条路径：
- 在**独立中断模式（unique IRQs）**下，将全局错误中断（gerror）的注册提前，然后检查 `is_kdump_kernel()`，若为真则直接返回，不再注册 EVTQ 和 PRIQ 的中断线程处理函数。
- 在**合并中断模式（combined IRQ）**下，修改 `arm_smmu_combined_irq_handler`，当处于 kdump 内核时，直接返回 `arm_smmu_gerror_handler` 的处理结果，而不再返回 `IRQ_WAKE_THREAD`，因为 EVTQ/PRIQ 已被禁用，对应的线程无需唤醒。

这一修复是对之前提交 b63b3439b856（"iommu/arm-smmu-v3: Abort all transactions if SMMU is enabled in kdump kernel"）的进一步完善，并标记为需要合入稳定内核 v6.12+。

## 参与讨论人员
- **Nicolin Chen** (NVIDIA) — 补丁作者，提交者。
- **Kevin Tian** (Intel) — 提供了 Reviewed-by 标签，表示已审查通过。

（在该邮件线程中未出现其他讨论者）

## 达成的结论
该补丁目前以 v6 版本呈现，且已获得 Kevin Tian 的审查通过（Reviewed-by），意味着改动内容和方案在审查者看来是正确的。但由于这是 rc 系列补丁之一，且并未出现进一步质疑，可以认为在技术方案上已达成共识，即需要在 kdump 内核中禁止 EVTQ/PRIQ 中断。不存在明显分歧。

## 下一步改进方向
该补丁属于一个补丁系列（v6, 3/7），因此：
- 需等待该系列中其余补丁的审查与合并流程。
- 可能需要进一步测试在真实 kdump 场景下的中断行为，确保不会引入其他异常（例如 gerror 中断的单独处理是否完全正确）。
- 由于包含 `cc: stable` 标签，未来可能需要向 v6.12 及更高版本的稳定内核提交回溯。

## 新增补丁
本次讨论中仅出现该补丁的新版本，即 **PATCH rc v6 3/7**，相比之前版本的变化未在邮件中详述，但根据片段可确认：
- 将 gerror 中断注册提前，并在 kdump 时跳过 EVTQ/PRIQ 中断的注册；
- 在 combined IRQ 处理函数中为 kdump 环境添加早期返回逻辑，不唤醒线程。

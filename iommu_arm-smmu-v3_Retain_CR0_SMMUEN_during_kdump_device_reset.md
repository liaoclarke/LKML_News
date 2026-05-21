# iommu/arm-smmu-v3: Retain CR0_SMMUEN during kdump device reset

---

## 更新 - 2026-05-20 10:03 UTC

## 核心话题
本补丁是arm-smmu-v3驱动kdump增强系列（v6）的第5个补丁，旨在解决kdump内核接管SMMU时因重置设备而中断正在进行的DMA的问题。在kdump场景下，崩溃内核已经配置了SMMU的流表、命令队列等，若kdump内核简单调用`arm_smmu_device_reset()`将CR0_SMMUEN清零并重写CR1/CR2/STRTAB_BASE，会导致所有在途DMA被终止，并使设备无法继续访问内存，严重降低kdump的可用性。此前的修复提交`b63b3439b856`（“iommu/arm-smmu-v3: Abort all transactions if SMMU is enabled in kdump kernel”）采取了直接中止所有事务的策略，虽然安全但并不理想。

本补丁提出了一种更优的“SMMU接管”模型：当检测到`ARM_SMMU_OPT_KDUMP_ADOPT`选项（由前序补丁基于`CR0_SMMUEN=1`且无`GERROR_SFM_ERR`的条件设置）时，保留SMMU的使能状态，跳过对STRTAB_BASE、CR1、CR2等寄存器的更新。依据Arm SMMUv3架构手册，当CR0_SMMUEN=1时，对这些寄存器的写入行为是“CONSTRAINED UNPREDICTABLE”，即硬件行为不可保证，强行写入可能导致状态错乱或DMA错误。因此，保留现有配置是最安全的选择，同时也使得在途DMA能够继续由原内核的流表进行地址翻译。

补丁的关键改动如下：
- 将`enables`变量初始化为0，从而在kdump路径中可以将`CR0_SMMUEN`保留为1并携带至后续命令队列使能阶段；
- 在设备重置函数开头读取CR0后，若处于kdump接管模式，则从原寄存器值中提取`CR0_SMMUEN`和`CR0_ATSCHK`，保存到`enables`中，绕过CR0清零与同步操作；
- 跳过STERTAB_BASE/CR1/CR2的写入，因为它们仅在SMMUEN=0时合法；
- 清除可能锁存的`GERROR`特定位（如CMDQP_ERR、EYENTQP_ERR等），避免因之前错误而导致新内核无法使用；
- 在启用命令队列时，通过`enables`保留SMMUEN，确保整个命令队列初始化完成后SMMU仍在运行。

该补丁由NVIDIA的Nicolin Chen提交，获得了Intel的Kevin Tian审查并添加了`Reviewed-by`标记。它是对kdump下IOMMU状态继承问题的进一步优化，标志着从“停止一切”演进到“无缝接管”，对于提高NVMe、GPU等高速设备在kdump下的可靠性有重要意义。补丁也标记为`Fixes`并建议回溯到v6.12+稳定版内核。

## 参与讨论人员
- Nicolin Chen (NVIDIA) — 补丁作者
- Kevin Tian (Intel) — 审查者，提供了Reviewed-by

## 达成的结论
本邮件是补丁提交，尚未见到后续讨论。从已有审阅标签来看，补丁设计已获得至少一位资深开发者的认可，但整体系列尚未完成全部审查，尚未合并到主线。结论可视为：补丁在技术方向上是合理的，并收到了积极的审阅反馈，但仍需等待系列其他部分审查完毕以及可能的重测。

## 下一步改进方向
- 完成整个7补丁系列的审查，确保各补丁之间的接口和逻辑一致性；
- 在实际硬件上测试kdump场景，验证SMMUEN保留后设备DMA的正确性及错误恢复；
- 检查与ATS、PCIe PTM等特性的交互，确保保留ATSCHK策略不会引起问题；
- 考虑对`GERROR`锁存位的清除是否足够充分，是否需处理更多错误状态；
- 若需要，将补丁拆分为更细粒度的提交以便回溯。
- 最终由ARM SMMU维护者（如Will Deacon）接纳并合并。

## 新增补丁
本邮件包含补丁 **v6 5/7**：`[PATCH rc v6 5/7] iommu/arm-smmu-v3: Retain CR0_SMMUEN during kdump device reset`  
该补丁在驱动重置函数中增加了对kdump接管模式的特殊处理，保留了CR0_SMMUEN位，跳过了在SMMU使能时非法写入的寄存器

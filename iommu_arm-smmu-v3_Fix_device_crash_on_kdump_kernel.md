# iommu/arm-smmu-v3: Fix device crash on kdump kernel

---

## 更新 - 2026-05-20 10:03 UTC

## 核心话题
本邮件讨论的是Linux内核ARM64架构下，ARM SMMUv3 IOMMU驱动在kdump内核启动时导致设备崩溃的问题及修复方案。当主内核发生崩溃并触发kdump启动时，可能有些PCIe设备仍在进行总线主控DMA（in-flight DMA）。当前的arm-smmu-v3驱动在kdump内核的探测阶段（probe）会执行侵袭性硬件重置：清除SMMU_CR0寄存器的SMMUEN位（关闭SMMU翻译）并将全局旁路属性（GBPA）设置为ABORT。这一重置行为在kdump场景下极具破坏性：

- 若GBPA被设为ABORT，所有正在进行的DMA事务都会被中断，硬件将产生致命的PCIe AER或SError，直接导致kdump内核panic；
- 若GBPA被设为BYPASS，那些输出地址（IOVA）恰好与物理地址1:1映射的in-flight DMA会绕过SMMU直接写入物理内存，从而污染物理内存，破坏kdump内核的正常运行。

为了安全吸收（absorb）这些in-flight DMA，kdump内核必须保留SMMUEN=1不变，并避免修改流表基址寄存器（SMMU_STRTAB_BASE），以使硬件能够继续使用已崩溃内核的页表进行地址翻译，直到各个端点设备的驱动重新初始化并静默其硬件。然而，ARM SMMUv3架构规范明确规定，在SMMUEN=1的情况下更新SMMU_STRTAB_BASE的行为是“不可预测”（UNPREDICTABLE）或被硬件直接忽略。因此，kdump内核别无选择，只能“接管”崩溃内核已经设置好的流表。

本系列补丁正是为了解决这一问题，核心思路是引入一个新的选项ARM_SMMU_OPT_KDUMP_ADOPT，当该选项启用时：

- 在arm_smmu_device_reset()中跳过对SMMUEN和流表基址的重置；
- 跳过EVENTQ/PRIQ的重新设置，包括其中断和中断处理函数；
- 将崩溃内核的流表通过memremap映射到kdump内核地址空间；
- 推迟默认域（default domain）的附加（attach），以保留流表项（STE）原有的内容，直到设备驱动显式请求重新附加。

为确保方案的安全性和可验证性，当前补丁仅针对一致性（coherent）SMMU实现。对于未启用ARM_SMMU_OPT_KDUMP_ADOPT的情况，驱动行为保持现状（自提交3f54c447df34以来的策略）：进行全重置，随后由驱动主动重新附加，可能会拒绝in-flight DMA。此外，该系列补丁依赖Jason Gunthorpe在v6.12合入的工作（commit 85196f54743d），该工作重组了struct arm_smmu_device的相关结构以支持此功能。

## 参与讨论人员
- Nicolin Chen (nicolinc@nvidia.com)，NVIDIA

## 达成的结论
本邮件为补丁系列的提交信，尚未见其他参与者的回复，因此未达成任何最终结论。补丁目前处于提案状态，等待社区审核和讨论。

## 下一步改进方向
1. 将方案拓展至非一致性（non-coherent）SMMU，补丁提交者指出现阶段仅为验证目的而仅支持一致性SMMU。
2. 需要更广泛的社区review，特别是ARM SMMUv3维护者和IOMMU子系统的核心开发者对“接管流表”这一非常规行为的评估与审核。
3. 实际测试验证，包括在真实硬件上触发kdump场景，确保in-flight DMA被安全吸收，不再导致panic或内存污染。
4. 可能需要讨论该功能是否应默认启用，或仅作为内核启动参数/设备树选项提供。

## 新增补丁
本邮件提交了补丁系列v6版本（共7个补丁），标题为“[PATCH rc v6 0/7] iommu/arm-smmu-v3: Fix device crash on kdump kernel”。由于邮件内容被截断，本版本相较v5的具体变更未能完全展示，但根据此前系列演化，预期包含对代码结构的优化、细节修正以及rebase至最新内核等改进。

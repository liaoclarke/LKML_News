# arm64: dts: qcom: glymur: Add GPU smmu node

---

## 更新 - 2026-05-22 15:41 UTC

## 核心话题
本邮件讨论的是为 Qualcomm Glymur 平台（某款骁龙 SoC）的 ARM64 设备树（DTS）添加 GPU SMMU（系统内存管理单元）节点。这是补丁系列 v5 的第 3/5 部分，由 Rajendra Nayak 提交，Akhil P Oommen 转发。补丁在 `glymur.dtsi` 中新增了 `adreno_smmu` 节点，位于 IOMMU 地址 `0x03da0000`，并声明了多个兼容字符串：`"qcom,glymur-smmu-500"`、`"qcom,adreno-smmu"`、`"qcom,smmu-500"` 和 `"arm,mmu-500"`。这些兼容性层级确保了内核能够匹配到适当的 GPU SMMU 驱动（如 arm-smmu 和 Adreno SMMU 实现），从而为 GPU 提供地址翻译和隔离保护。

该节点定义了 SMMU 的寄存器范围大小为 `0x40000`，`#iommu-cells = <2>` 表示需要两个参数来指定设备的主 SID 和辅助 SID。`#global-interrupts = <1>` 意味着第一个中断为全局中断，其余为上下文中断。邮件中列出了一长串中断号（GIC SPI），但由于邮件截断，未能完整展示中断列表。从可见部分可以识别出多个上下文中断（如 SPI 678-688）以及若干额外的中断（如 SPI 422、476、574-577、660、662、665 等），这些中断用于报告 SMMU 上下文错误、性能监控等事件。

该补丁的技术动机是使能 Glymur 平台的 GPU 地址空间管理，这是 GPU 驱动程序正常工作的前提。没有 SMMU 节点，GPU 将无法进行 DMA 映射和隔离，导致系统稳定性或安全性问题。该补丁已获得 Konrad Dybcio 和 Dmitry Baryshkov 的审核通过标签，表明其符合 Qualcomm 设备树的规范，且与现有 adreno_smmu 驱动兼容。虽然邮件未提及具体 SoC 型号，但 Glymur 很可能对应骁龙 8 Elite 或类似高端芯片，其 GPU 采用 Adreno 架构，需通过 SMMU 实现虚拟化或保护。补丁本身的设备树描述较为标准，与其它 QCOM 平台的 GPU SMMU 节点结构一致。

## 参与讨论人员
- Rajendra Nayak (Qualcomm) — 原始补丁作者
- Akhil P Oommen (Qualcomm) — 补丁提交者
- Konrad Dybcio (Qualcomm) — 审核者（Reviewed-by）
- Dmitry Baryshkov (Qualcomm) — 审核者（Reviewed-by）

（本线程仅包含补丁邮件，无其他讨论者）

## 达成的结论
此邮件为单向补丁提交，未出现后续讨论或反对意见，因此“结论”并非来自多边协商。从流程上看，补丁已获得两名维护者的 Review 标签，且以 v5 版本发送至公共列表，表明其已具备合入条件，只是等待维护者合并。没有争议点或分歧，因此可以认为该节点添加已达成共识，即同意该设备树描述的正确性和必要性。

## 下一步改进方向
由于邮件内容被截断，中断列表不完整，下一步可能需要检查完整补丁以确认所有中断声明正确，特别是全局中断与上下文中断的计数是否与 `#global-interrupts` 匹配。后续动作包括：
- 维护者或测试者需验证补丁在全系列中的上下文（前三部分的依赖关系）。
- 确认 Glymur 平台的 GPU SMMU 驱动绑定是否已通过另一补丁更新（如新增 `qcom,glymur-smmu-500` 兼容项）。
- 若有后续版本（v6），需整合可能的反馈，例如中断名称的描述、power-domains 或 clocks 的关联（如 GPUCC 交互），但当前补丁未涉及这些。
- 总体等待维护者应用该系列。

## 新增补丁
本邮件即为新增补丁，版本为 **PATCH v5 3/5**。该版本相对于之前版本的变更未知（邮件历史未提供），但从系列角度推断，v5 可能修复了 v4 中的设备树绑定或节点属性问题。此部分仅负责添加 Glymur 的 GPU SMMU 节点，无其他补丁在此线程中发布。

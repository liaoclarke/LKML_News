# KVM: arm64: gic-v5: Define remaining IRS MMIO registers

---

## 更新 - 2026-05-21 14:50 UTC

## 核心话题
本邮件串讨论的是在 Linux KVM arm64 虚拟机中模拟 GICv5 中断翻译服务 (Interrupt Translation Service, IRS) 所需的寄存器定义补丁。Sascha Bischoff 最初的补丁 (PATCH 18/43) 试图补全 `arm-gic-v5.h` 头文件中尚未定义的 IRS MMIO 寄存器，理由是之前的定义仅按需添加，而为了在 KVM 中对 IRS 进行完整的 MMIO 模拟，必须引入完整的寄存器集合。

Marc Zyngier 审阅后提出了两个关键意见。其一，寄存器定义的添加风格必须统一：要么在一个补丁中一次性引入所有定义，要么将每个定义伴随实际使用它的代码一同添加，而他个人强烈倾向于前者（"My preference goes with the former"）。其二，他对补丁中新增的 `GICV5_IIDR_IMPLEMENTER_ARM` (值为 0x43b) 表示犹豫。他指出，在 GICv2/v3 中已经用同样的方式将 KVM 模拟的 GIC 标记为 ARM 实现，但这实际上并非真的 ARM 实现。更重要的是，这种 ARM 特定的编码本不应该存在于这个公共的头文件中——它只对 KVM 的实现有意义，应当保留在 KVM 自身的代码里（"the ARM encoding should not leave in this file -- it is only used for the KVM implementation, and everything else should be..."）。

Sascha 接受了全部反馈。他明确表示已按第一种风格重新整理整个系列，将该补丁调整为系列的前几个改动之一，并将所有 GICv5 寄存器定义集中在一块提前引入。同时也去除了有争议的 `GICV5_IIDR_IMPLEMENTER_ARM` 定义，在 v2 补丁的片段中已看不到该常量，仅保留了架构相关的 `AIDR` 和 `IIDR` 寄存器偏移地址，而不再在公共头文件中硬编码具体的 ARM 实现者 ID。

## 参与讨论人员
- Sascha Bischoff (Arm)
- Marc Zyngier (KVM/arm64 维护者，发件地址未显示，但基于上下文为代码审阅者)

## 达成的结论
讨论达成一致结论。Sascha 采纳了 Marc 的两项建议：
1. 寄存器定义的添加风格统一为“一次性全部添加”，在新的 v2 系列中将所有 IRS 寄存器定义合并到一处，作为早期补丁提交。
2. 从公共头文件 `include/linux/irqchip/arm-gic-v5.h` 中移除 `GICV5_IIDR_IMPLEMENTER_ARM` 等 ARM 专用实现者常量，这些值只应在 KVM 模拟层的私有实现中定义和使用，不应污染架构头文件。

## 下一步改进方向
Sascha 需要继续完成 v2 系列中后续使用这些寄存器定义的补丁，确保 KVM 的 IRS 模拟实现正确引用新添加的寄存器偏移地址，并在 KVM 内部自行定义模拟所需的 `IIDR` 实现者字段值，而不再依赖公共头文件。Marc 后续可能需要对 v2 完整系列进行审阅，重点检查 KVM 模拟是否正确处理了这些新增寄存器，以及 ARM 实现者 ID 是否确实被合理隔离在 KVM 代码中。

## 新增补丁
- **[PATCH v2 04/39] KVM: arm64: gic-v5: Define remaining IRS MMIO registers**  
  本版本相对于 v1 补丁进行了重构和扩充。主要变化包括：将寄存器定义一次性完整添加（由原来的 105 行增加至 203 行左右），补充了 `GICV5_IRS_IDR3`、`IDR4`、`IIDR`、`AIDR`、`SPI_VMR`、`SPI_DOMAINR`、`SPI_RESAMPLER`、`VMT_BASER` 等大量缺失的寄存器偏移量；同时移除了 v1 中引入的 `GICV5_IIDR_IMPLEMENTER_ARM` 常量，仅保留寄存器地址定义，符合将实现者 ID 留在 KVM 内部的共识。

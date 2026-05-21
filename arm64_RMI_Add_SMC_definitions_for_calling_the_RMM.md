# arm64: RMI: Add SMC definitions for calling the RMM

---

## 更新 - 2026-05-21 16:33 UTC

## 核心话题
该邮件线程围绕为 Linux 内核 ARM64 架构引入 Realm Management Monitor（RMM）的 SMC 调用定义展开，对应补丁 `[PATCH v14 04/44] arm64: RMI: Add SMC definitions for calling the RMM`。该工作服务于 ARM 机密计算架构（Confidential Compute Architecture, CCA），旨在通过定义完整的 SMC 接口，使主机操作系统能够与 RMM 固件进行通信，从而实现对“领域”（Realm）虚拟机的生命周期管理、内存隔离与执行环境控制。

补丁的核心是在 `arch/arm64/include/asm/rmi_smc.h` 中新增一个头文件，集中定义了与 RMM 交互所需的 SMC 功能号、参数结构体、返回值与常量。从提交信息可以看出，该实现严格遵循 ARM 规范 DEN0137 版本 2.0‑bet1（文档链接见于补丁描述）。开发者 Steven Price 在 v14 版本中相比前版做出了多项针对性修正，例如：将 `ripas_value` 在 `rec_exit` 结构中的类型从 `u64` 改为 8 位并添加填充，以符合规范；引入 `RMI_PERMITTED_GICV3_HCR_BITS` 宏，明确列出 RMM 允许修改的 GICv3 HCR 寄存器位；为 `REC_ENTER_xxx` 系列宏添加 `FLAG` 后缀以增强可读性；排序 SMC 号；重命名 `SMI_RxI_CALL` 为 `SMI_RMI_CALL` 并调整 `REC_GIC_NUM_LRS` 等常量名称，使其更准确地反映实际硬件能力。这些改动体现了对 ABI 稳定性、规范一致性与代码清晰度的持续追求。

由于提供给分析工具的邮件正文被截断，无法看到 Gavin Shan 与 Marc Zyngier 的具体审阅意见。但已知 Marc Zyngier 作为 ARM 平台与中断子系统维护者，通常会关注虚拟 GIC 相关定义以及 HCR 等控制位的合理性。Gavin Shan 此前也多次参与该系列补丁的审查，可能会对结构体布局、命名约定或与 KVM 集成的细节提出建议。整体上，该线程是补丁集评审过程中的一个环节，核心议题就是确保 RMI SMC 定义精确匹配规范，并为后续的领域内存管理、调度和控制接口奠定基础。

## 参与讨论人员
- **Steven Price** （Arm，补丁作者）
- **Gavin Shan** （邮件中提到曾发送审核意见，具体所属机构未在片段中体现）
- **Marc Zyngier** （Arm / kernel.org 维护者）

## 达成的结论
由于邮件内容大面积被截断，无法从现有片段中辨别是否已就任何技术细节达成明确共识。从上下文看，该讨论仍在常规补丁审查流程中，尚未出现表示完全认可或要求彻底变更的结论性回复。

## 下一步改进方向
后续需要根据审查成员（如 Marc Zyngier、Gavin Shan 等）提供的具体技术反馈，对 `rmi_smc.h` 中的宏定义、结构体字段及注释进行调整，确保与 RMM 规范的无缝对齐，并满足内核编码风格与可维护性要求。补丁作者可能还需要提供更详尽的移植说明，或者配合测试用例来证明这些 SMC 定义在实际 CCA 硬件或模拟环境中的正确性。

## 新增补丁
本邮件线程本身未发布新版本补丁，仅包含针对 v14 版本的评审交流。

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

---

## 更新 - 2026-05-22 10:58 UTC

## 核心话题
该邮件讨论的是针对 ARM64 架构的 Linux 内核补丁“arm64: RMI: Add SMC definitions for calling the RMM”（v14 系列第 4/44），由 Steven Price 提交。补丁的核心目的是在 arch/arm64/include/asm/rmi_smc.h 中添加一组 SMC（Secure Monitor Call）调用定义，用于主机与 RMM（Realm Management Monitor）进行通信。RMM 是 ARM 机密计算架构（ARM CCA）中的关键组件，负责管理 Realm（机密虚拟机）的生命周期、内存隔离和状态转换。该补丁严格基于 ARM 规范 DEN0137 2.0-bet1 版本（文档链接已给出），定义了 RMI（Realm Management Interface）的 SMC 调用号、返回状态码、以及相关数据结构（如 rec_enter、rec_exit 等），其中包含对中断控制器虚拟化（GICv3 HCR bits）、PMU 溢出状态、以及 RMM 特性寄存器等细节的精确映射。

从补丁的变更历史（Changes since v13/v12/v9...）可以看出，这项工作已经历了长期迭代，每一版都紧跟 RMM 规范的演进（从 1.0-rel0-rc1 到 2.0-bet1），并修正了诸如 ripas_value 字段大小、PAC 位定义、标志位命名（添加 FLAG 后缀）、最大 List Register 数量处理（REC_MAX_GIC_NUM_LRS）等与规范对齐的问题。Marc Zyngier 在邮件中回复了 Steven Price 的先前回应，但后续的具体技术审查意见被截断（邮件标注 “[...truncated...]”）。从上下文推断，Marc 可能正在审查该补丁，并可能针对规范细节、宏命名或数据结构布局提出进一步意见，但截断内容使我们无法获知具体争论点。

## 参与讨论人员
- Steven Price (steven.price@arm.com, Arm)
- Marc Zyngier (maz@kernel.org, 内核维护者/独立开发者)

## 达成的结论
由于邮件内容在 Marc Zyngier 回复的开头处被截断，无法看到后续的技术讨论和回应，因此在当前提供的片段中未能达成任何明确结论。没有出现 Acked-by、Reviewed-by 或明确的反对意见。

## 下一步改进方向
因缺乏完整的讨论内容，无法确定具体的下一步。根据补丁的迭代性质（v14）和规范仍在 beta 阶段（2.0-bet1），预计 Steven Price 可能需要根据 Marc 的审查意见或规范更新进行修订，可能涉及进一步收紧宏定义、完善注释或调整与后续补丁的接口协调。

## 新增补丁
本邮件片段中未发布新版本的补丁，当前讨论仍围绕 v14 的 04/44 补丁进行。

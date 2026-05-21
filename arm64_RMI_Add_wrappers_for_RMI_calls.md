# arm64: RMI: Add wrappers for RMI calls

---

## 更新 - 2026-05-21 16:44 UTC

## 核心话题
本邮件讨论聚焦于 ARM64 架构下 Realm 管理接口（RMI）调用的封装实现，这是 Arm CCA（机密计算架构）中 Realm 支持的内核补丁系列（v14）中的第 5 个补丁。补丁作者 Steven Price 为 RMI 命令添加了 wrapper 函数，这些命令用于 Guest Realm 与 Realm 管理监视器（RMM）之间的交互。Wrapper 的目的是简化调用点代码，并统一处理 RMM 返回的错误码，正如提交信息中所述：“The wrappers make the call sites easier to read and deal with the boiler plate of handling the error codes from the RMM.”

从补丁内容可见，它在 `arch/arm64/include/asm/rmi_cmds.h` 中定义了大量内联函数，每个 wrapper 对应一条 RMI 命令（如 rmi_rtt_destroy、rmi_rtt_read_entry 等），并借助 `arm_smccc_1_1_invoke` 或 `arm_smccc_1_2_invoke` 发起 SMCCC 调用。补丁还引入了 `struct rtt_entry` 和 `struct rmi_sro_state` 等数据结构，以及类似 `rmi_smccc(...)` 的宏。该系列已演进到 v14，基于 RMM v2.0-bet1 规范，部分支持 SRO（地址列表操作），但代码中仍留有 FIXME 标记表示 SRO 支持未完成。

技术动机在于：直接使用原始 SMCCC 调用会使调用点充斥大量寄存器赋值和返回值解析，降低可读性并增加出错概率。通过为每条 RMI 命令提供语义清晰的 wrapper，内核代码能更清晰地表达“读取 RTT 条目”或“销毁 RTT”等操作，同时 wrapper 内部统一进行状态码检查，返回有意义的错误号，这符合内核中类似接口（如 PSCI、SDEI）的惯用模式。

讨论中的关键论点来自两位 reviewer：
- **Gavin Shan** 对文档注释提出意见，从截断内容 “In most cases, the parame…” 推测，他可能指出 wrapper 参数命名的描述一致性问题，或注释未充分说明某些特殊情况。
- **Marc Zyngier** 的评论被截断，但引用上下文显示他关注了 `rmi_smccc` 宏的定义（使用了 `do { ... } while (RMI_RETURN_STATUS(re...)`），可能指出宏的安全性或风格问题，例如宏中的返回值处理是否可靠，或是否需要改为 static inline 函数以增强类型安全。Steven 的回复开头为 “On 21/05/2026 13:49, Marc Zyngier wrote:”，随后再次引用 Marc 邮件并开始回应，但具体回应内容也被截断，未能完整呈现。

总体而言，讨论围绕 wrapper 实现的代码质量、注释准确性和宏设计展开，未出现根本性架构反对意见。

## 参与讨论人员
- **Steven Price** (

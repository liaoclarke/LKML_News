# PCI: host-generic: Simplify return value handling in pci_host_common_parse_port(s)

---

## 更新 - 2026-05-22 11:43 UTC

## 核心话题
该补丁旨在简化 `pci-host-common.c` 中 `pci_host_common_parse_port()` 与 `pci_host_common_parse_ports()` 两个函数的返回值处理逻辑。当前代码在解析 PCI 根端口的 PERST# 资源时，会在公共辅助函数中检查 RC 节点本身的绑定情况（legacy binding），并依据是否有 PERST# 出现在 RC 节点而返回 -ENODEV，迫使调用者回退到旧有绑定方式。补丁作者 Sherry Sun 认为，“pci_host_common_parse_port() shouldn't check the RC-level binding. That's a policy decision that belongs to the caller, not this common helper.” 也就是说，对 RC 级绑定的判断属于调用者的策略，不应内嵌于通用的解析函数中。

补丁的技术动机是让这些公共函数职责更单一：`pci_host_common_parse_port()` 仅负责从 Root Port 及其子节点解析属性，不再关心 RC 节点的状态。相应地，`pci_host_common_parse_ports()` 在没有找到任何端口时，也应当返回 0 而非错误码，因为“no ports found”并不属于真正的错误——某些平台可能根本不需要用这种方式描述端口。补丁描述中明确写道：“both functions won't return failure for 'property not found' or 'port not found', they purely returns 0 on success and a negative error code on real failures.” 这样，调用方可根据自身需求决定如何处理“未找到端口”的情形，而不会被一个并非错误的负返回值强制进入回退逻辑。

代码变更删除了原有在 `pci_host_common_parse_port()` 内对 `port->perst` 列表为空的判断，该判断会检查 RC 节点是否直接含有 PERST# 属性并返回 -ENODEV。将这些逻辑移除后，函数变得更简洁，错误语义也更清晰。这属于 PCI 主机通用驱动在 ARM64 架构下的代码清理与改进，旨在提高代码可维护性和灵活性，避免公共工具函数做出过多假设。

## 参与讨论人员
- **Sherry Sun** (sherry.sun@nxp.com / sherry.sun@oss.nxp.com)，来自 NXP，补丁作者与提交者。

（该邮件线程中仅有补丁投递，尚无回复或讨论人员。）

## 达成的结论
邮件线程中仅包含单封补丁邮件，未见任何回复或 Ack/Nack，因此 **未达成共识**。补丁处于等待社区审阅的初始阶段。

## 下一步改进方向
1. **社区审核**：需要 PCI 子系统维护者及其他开发者审阅该补丁，确认将 RC 级绑定检查提升至调用者的做法是否合理，以及是否会影响现有调用路径（如 `pcie-rcar-host.c` 等）。
2. **补充配套变更**：该系列标记为 `[PATCH 1/2]`，第二补丁未在截断的邮件中展示，可能涉及对应调用方的策略调整，需要一并审阅才能判断整套改动的完整性。
3. **测试覆盖**：建议在无 PERST#、PERST# 仅在 RC 节点、仅在 RP 节点等多种设备树配置下进行回归测试，确保原有回退路径不受破坏。

## 新增补丁
- **[PATCH 1/2]**（v1）：PCI: host-generic: Simplify return value handling in pci_host_common_parse_port(s)  
  简化了 `pci_host_common_parse_port()` 和 `pci_host_common_parse_ports()` 的返回值，删除了对 RC 节点绑定的检查，使两个函数在未找到属性或端口时返回 0，真正的错误才返回负值。  
  （本邮件仅包含第 1/2 补丁的片段，第 2/2 补丁内容未出现在线程中。）

---

## 更新 - 2026-05-22 06:20 UTC

## 核心话题
本邮件的讨论围绕 Sherry Sun 提交的一个补丁（[PATCH 1/2] PCI: host-generic: Simplify return value handling in pci_host_common_parse_port(s)）展开。该补丁旨在简化 `pci_host_common_parse_port()` 和 `pci_host_common_parse_ports()` 两个函数的返回值处理逻辑，使其职责更清晰。补丁的核心思想是：`pci_host_common_parse_port()` 不应检查 RC（Root Complex）级别的绑定，这一策略决策应属于调用者而非这个通用辅助函数。因此，该函数只负责从 Root Port（及其子节点）解析属性，不再检查 RC 节点；同时，`pci_host_common_parse_ports()` 在未找到任何端口时直接返回 0，因为缺少端口并不构成错误。这样一来，两个函数都不会因为“属性未找到”或“端口未找到”而返回失败，仅在真正出错时返回负的错误码。

邮件中，Richard Zhu 对该补丁进行了代码审查，但并未质疑补丁的技术实质，而是指出了补丁描述（commit message）中的几处英文笔误：
- “to only parses” 应改为 “to only parse”
- “Root Port(and its children)” 中 “Port” 后缺少空格
- “returns” 应改为 “return”

Sherry Sun 回复表示将修复这些问题。这次讨论虽然不长，但反映出补丁的技术方向获得了认可，只需修正形式上的瑕疵。

## 参与讨论人员
- Sherry Sun (NXP)
- Richard Zhu（署名 Best Regards Richard Zhu，可能同为 NXP）

## 达成的结论
已就补丁的文档/注释修正达成一致。Sherry Sun 接受了 Richard Zhu 指出的所有英文语法和格式问题，将进行修复。补丁本身的逻辑简化思路未引起争议，可视为得到了初步认可。

## 下一步改进方向
需要 Sherry Sun 发布修复上述语法与格式问题的 v2 版本补丁。具体包括：
- 将 “to only parses” 修正为 “to only parse”
- 在 “Root Port” 和括号之间添加空格，即 “Root Port (and its children)”
- 将 “returns” 修正为 “return”

修复后，补丁可再次提交以供后续审核或合入。

## 新增补丁
本线程中尚未出现新版本补丁。预期下一版本为 v2，其变更仅限于上面指出的三处描述/注释修正，核心代码逻辑预计保持不变。

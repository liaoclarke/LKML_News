# PCI: imx6: Improve PERST# fallback logic

---

## 更新 - 2026-05-22 11:43 UTC

## 核心话题
该讨论围绕 PCIe 控制器驱动 imx6 中 PERST#（PCIe 复位信号）的 GPIO 回退逻辑展开。补丁作者 Sherry Sun 指出，现有公共辅助函数 `pci_host_common_parse_port()` 在解析设备树时，通过检查 RC（根端口）节点上是否存在 “reset-gpios/reset-gpio” 属性来决定是否回退到传统的 RC 级别绑定，并在找不到时返回 `-ENODEV` 的做法存在问题。作者认为这种策略决策应由调用者（即具体的驱动，如 imx6）负责，而非放在通用辅助函数中，因为这属于策略层面的判断，不应耦合在共同代码里。该补丁集旨在改进这一回退逻辑：首先简化 `pci_host_common_parse_port()` 的返回值处理，使其不再进行策略判断；然后在 imx6 驱动中新增 `imx_pcie_perst_found()` 函数来检查解析结果，从而将回退决策从通用代码移到驱动内部，使公共辅助函数更加纯粹，责任分离更清晰。补丁基于 commit 550604d6c9b9，涉及文件 `pci-host-common.c` 和 `pci-imx6.c`，共删除 32 行，新增 22 行，属于代码重构与优化性质。

## 参与讨论人员
- Sherry Sun (OSS) <sherry.sun@oss.nxp.com>（来自 NXP，补丁作者）

## 达成的结论
该邮件为补丁系列的封面（PATCH 0/2），尚未出现其他讨论者的回复，因此尚未形成任何共识或结论。作者提出了改进思路并提交了代码修改，等待社区反馈和审阅。

## 下一步改进方向
- 等待社区相关人员（如 PCI 维护者、i.MX 驱动维护者）审阅补丁内容，确认将回退逻辑移至驱动程序级的做法是否合理。
- 可能需要提供更详细的变更说明，解释 `imx_pcie_perst_found()` 的具体实现及其如何解析 `reset-gpios` 的结果。
- 确保修改后的代码在各类设备树配置（是否提供 RC 级或控制器级 GPIO 等）下均能正确工作，不影响现有功能。
- 如果评审通过，可能需要将补丁纳入 PCI 子系统的下一个合并窗口。

## 新增补丁
本线程中作者发布了以下两个补丁（以 PATCH 系列形式提交）：
- [PATCH 1/2] PCI: host-generic: Simplify return value handling in pci_host_common_parse_port(s)
- [PATCH 2/2] PCI: imx6: Add imx_pcie_perst_found() to inspect the parsed result

均为第一版（v1），未出现后续修订版本。

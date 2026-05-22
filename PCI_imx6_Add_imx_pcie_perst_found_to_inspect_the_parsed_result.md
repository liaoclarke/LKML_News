# PCI: imx6: Add imx_pcie_perst_found() to inspect the parsed result

---

## 更新 - 2026-05-22 11:43 UTC

## 核心话题
本补丁是针对 NXP i.MX6 PCIe 主机控制器驱动的一次修正，源于 `pci_host_common_parse_port()` 函数行为的变更。在旧代码中，该函数会在缺少设备树中的“perst”属性时返回 `-ENODEV`，驱动据此判断是否需要回退到传统的设备树绑定。但修改后的通用解析接口不再将“属性未找到”视为错误（即不返回 `-ENODEV`），而是成功返回 0 并允许调用者自行检查解析结果。因此，原驱动的错误处理路径 `if (ret != -ENODEV)` 已无法正确捕获该场景，必须设计新的检查机制。

补丁作者 Sherry Sun 为此引入 `imx_pcie_perst_found()` 辅助函数，遍历 `pci_host_bridge->ports` 链表，检查是否存在已填充的 `perst` 链表节点。若未找到任何 `perst` 信息，则说明当前设备树未使用新的根端口绑定，驱动需安全降级至传统绑定 `imx_pcie_parse_legacy_binding()` 以保证向后兼容。这种“先尝试通用解析，再检查结果，最后回退”的流程相比旧代码更加清晰：严格区分“解析失败”（`ret != 0`，直接报错返回）与“解析成功但无 perst 节点”（通过新函数判断后回退）两种情况，避免因 `pci_host_common_parse_ports()` 返回值的语义变化而错过有效回退，或错误地将真正的解析失败当作可选绑定缺失处理。

补丁体现的核心技术动机是：在 ARM64 PCIe 驱动框架优化过程中，主机桥端口解析接口朝着更精细化的方向演进，不再使用 `-ENODEV` 作为“可选特性缺失”的信号，转而要求驱动自助决策。驱动侧需要在不破坏现有设备树兼容性的前提下跟进这一变化。该系列补丁（[PATCH 1/2] 可能修改了通用解析函数）与 IMX6 驱动的适配共同保证了过渡的平滑性，同时也提升了代码的可读性和鲁棒性。

## 参与讨论人员
- Sherry Sun (NXP) <sherry.sun@nxp.com>, <sherry.sun@oss.nxp

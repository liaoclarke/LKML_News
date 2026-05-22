# arm_mpam: Disable reqPARTID expansion when Narrow-PARTID is unavailable

---

## 更新 - 2026-05-22 17:57 UTC

## 核心话题
本邮件线程围绕 ARM64 体系结构下 MPAM（Memory Partitioning and Monitoring）特性的一个补丁（PATCH v8 03/10）展开，主题是“在没有 Narrow-PARTID 支持时禁用 reqPARTID 扩展”。补丁作者 Zeng Heng 提出：当系统中的某些内存系统组件（MSC）不支持 Narrow-PARTID，同时又采用了基于百分比（或其他有状态）的节流控制时，resctrl 就无法正确地将控制组配置映射到多个 PARTID，因此需要在这种条件下禁用 reqPARTID 的多重分配能力，回退到仅使用 intPARTID 数量，从而禁止监控组的 reqPARTID 扩展。

维护者 James Morse 在回复中指出了几个关键技术点。首先，他反对使用“stateless”（无状态）一词来描述控制类型，建议采用更贴近 MPAM 硬件行为的“aliasing / non-aliasing”术语，因为 MPAM 的资源控制是定态分数、位图或成本/权重，而非 x86 的百分比节流。Zeng Heng 立即接受了这一术语建议，并承认了原先术语中的 x86 色彩。其次，James 认为补丁的思路“上下颠倒”了：正确的做法不是因缺少 Narrow-PARTID 而普遍禁用 reqPARTID 扩展，而是只在极少数“不存在任何需要丢弃的控件”的平台上才启用此功能。他还明确反对将这一检测逻辑添加到 `resctrl_arch_system_num_rmid` 这类接口中。邮件在此处被截断，但可以推断 James 要求将 enable/disable 的决策条件重新设计，并与更上层的使能逻辑对齐，而非在底层函数中硬性降级。

## 参与讨论人员
- **Zeng Heng** (zengheng@huaweicloud.com): 补丁作者，来自华为云。
- **James Morse**: 内核 MPAM 子系统的维护者/核心开发者，邮件中未提及所属公司，但通常代表 Arm 或 Linux 社区视角。

## 达成的结论
从现有邮件片段来看，双方在术语上快速达成一致（采用 aliasing/non-aliasing），但在功能设计和实现路径上存在明显分歧，且未看到 James 对 Zeng Heng 的认同或折中方案。由于邮件被截断，无法判断后续是否达成妥协或出现新的论证。当前可认为：术语更改已达成共识，但关于禁用条件、检测位置以及“仅少数平台启用”的设计原则尚未达成统一结论，讨论仍处于技术辩论阶段。

## 下一步改进方向
Zeng Heng 需要根据 James Morse 的反馈进行实质性修改：
1. **采用正确术语**：用 “non-aliasing” 替换 “stateless”，并在代码注释和提交信息中统一。
2. **重新设计启用条件**：不再以“缺少 Narrow-PARTID 且有百分比控制”作为禁用条件，而是反向设计，仅为那些“没有任何需要丢弃的控制”的有限平台明确启用 reqPARTID 扩展功能。
3. **调整代码插入点**：移除在 `resctrl_arch_system_num_rmid` 或类似底层函数中植入降级逻辑，将 enable/disable 检查提升到更早的初始化阶段或特性使能判断层。
4. **补充测试与平台验证**：需要确认目标平台确实符合“无需要丢弃的控制”这一严格条件，并测试新条件判断的准确性。

## 新增补丁
在本线程片段中，未出现补丁的新版本。当前讨论基于 v8 系列，后续可能需要提交 v9 以体现上述设计变更。

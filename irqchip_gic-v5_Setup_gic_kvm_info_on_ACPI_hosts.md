# irqchip/gic-v5: Setup gic_kvm_info on ACPI hosts

---

## 更新 - 2026-05-21 14:50 UTC

## 核心话题
本邮件是Sascha Bischoff提交的针对ARM64架构下GICv5中断控制器的补丁，属于一个39个补丁的系列中的第3个，版本为v2。其核心问题在于：当系统以ACPI方式启动时，GICv5的中断控制器初始化无法向KVM提供vGIC（虚拟GIC）所需的关键信息，导致KVM无法在ACPI主机上正常探测并初始化虚拟GIC。

在设备树（DT）启动路径中，`gic_of_setup_kvm_info()` 已经完成了这项工作：它从设备树节点解析维护中断（maintenance interrupt），并将IRS（Interrupt Routing Service）的基地址、一致性标志、中断号填入全局的 `gic_v5_kvm_info` 结构，从而使KVM能够获取 `GIC_V5` 类型的主机信息。但ACPI路径仅调用了 `gic_acpi_init` 完成基础初始化和ACPI IRQ模型的安装，完全跳过了KVM相关信息的填写，这导致ACPI平台上KVM探测vGIC失败。

补丁的解决方案是为ACPI路径添加与DT路径等价的KVM信息配置。具体实现包括：
- 将原`gic_of_setup_kvm_info`中的KVM信息填充逻辑重构为一个通用的`gic_setup_kvm_info(unsigned int maint_irq)`函数，去除了对设备树节点的依赖，改为由调用者传入已解析的维护中断号。
- 新增ACPI解析部分：解析MADT表中所有GICC子表，提取维护中断字段（Maintenance Interrupt），并要求所有相关GICC条目中的该值保持一致（不匹配时给出警告或错误），然后将该中断号转换为GICv5 PPI编码的GSI（通过`acpi_register_gsi`之类机制），最后连同IRS基地址、非一致性标志等信息填入`gic_v5_kvm_info`。
- 兼容原生GICv5无需维护中断的情况（当未使用兼容GICv3的CPU接口时），保持原有对无维护中断的处理。

邮件中贴出的补丁片段显示了一个`gic_setup_kvm_info`函数的开始，它接收`maint_irq`参数，从`gicv5_irs_get_chip_data()`获取IRS数据，并检查有效性。函数体在“[truncated]”处截断，但可推断后续会设置`gic_v5_kvm_info`的各个字段并调用`kvm_setup_vgic`或类似函数将信息传递给KVM。

该补丁对于使能ACPI系统的虚拟化支持至关重要，因为目前ARM服务器大多采用ACPI启动，缺乏该修补将阻碍KVM在ARM ACPI平台上的应用。

## 参与讨论人员
- Sascha Bischoff (Arm)

从提供的邮件片段来看，仅包含补丁提交者的单封邮件，未见其他人员的回复或评论，因此该线程实际只有一名参与者。

## 达成的结论
本线程仅为补丁提交，未出现讨论、反对或审查意见，因此未达成任何实质性的技术共识或结论。该补丁处于等待社区审查的状态。

## 下一步改进方向
- 需要社区维护者（如Marc Zyngier）或其他ARM KVM领域开发者对该补丁进行审查，检查ACPI MADT解析逻辑的正确性、与现有ACPI IRQ映射机制的兼容性，以及是否引入了潜在的竞态或初始化顺序问题。
- 可能需要补充更多注释，说明为何要求所有GICC条目的维护中断值必须一致，以及这一约束是否符合ACPI规范。
- 如果原生GICv5无维护中断的情况处理不够清晰，可能需要改进该逻辑或添加更多文档。
- 该补丁作为39个补丁系列的组成部分，需要与系列中的其他更改保持协调，尤其依赖于前序补丁提供的GICv5 KVM基础设施或ACPI表格导出的接口。
- 不排除在v3中根据审查反馈进行调整。

## 新增补丁
- [Patch v2 03/39] irqchip/gic-v5: Setup gic_kvm_info on ACPI hosts  
  与v1相比的具体变更未在本邮件中说明，但邮件题目标明为v2，表明该补丁至少已经历一轮修订。v2的改动可能根据前一轮的审查意见进行了重构，将KVM信息设置抽象为通用函数，以同时服务于DT和ACPI路径。

# arm64: RMI: Check for RMI support at init

---

## 更新 - 2026-05-21 16:49 UTC

## 核心话题
本补丁（v14系列的第6个补丁）旨在为ARM64架构添加RMI（Realm Management Interface）支持的初始化检查。核心动机是在系统启动早期探测RMM（Realm Management Monitor）是否存在且版本兼容，并读取前两个特性寄存器（rmm_feat_reg0/1），供后续代码使用。  
一个关键设计变动是，将RMI的基础探测从原来纯粹依赖KVM的路径迁移到`arch/arm64/kernel/rmi.c`，作为内核通用功能。理由是RMI将不仅服务于KVM虚拟化，还会用于其他非KVM特性，因此即使内核未编译KVM支持，RMI相关初始化也应可用。  
技术实现上：  
- 首先通过`read_sanitised_ftr_reg(SYS_ID_AA64PFR0_EL1)`读取CPU特性寄存器，检查硬件是否支持RME（Realm Management Extension），若不支持则直接返回`-ENXIO`。  
- 支持RME后，通过`SMC_RMI_VERSION`调用固件接口，传递宿主期望的ABI版本（`RMI_ABI_VERSION`），并检查返回值：若返回`SMCCC_RET_NOT_SUPPORTED`，则同样返回`-ENXIO`；否则比对主次版本号，确保版本兼容。  
- 若版本兼容，再调用`SMC_RMI_FEATURES`读取两个特性寄存器，存入全局变量`rmm_feat_reg0/1`。  
讨论的触发点在于Gavin Shan对补丁的审查意见（邮件片段中截断），推测涉及版本检查的健壮性、与SMCCC交互的边界条件，以及将这部分代码移出KVM目录后是否所有依赖都得到正确处理。Marc Zyngier的回复也出现在邮件首部（片段截断），可能提出了对实现方式或安全性的进一步建议。

## 参与讨论人员
- Steven Price (ARM Ltd)
- Gavin Shan
- Marc Zyngier (kernel.org)

## 达成的结论
从现有邮件片段看，讨论尚未达成明确共识。Gavin Shan提出了审查意见，Steven Price给予了回复（回复内容因截断未知），Marc Zyngier也加入了讨论，说明存在需要澄清或修改的技术点，协商仍在继续。

## 下一步改进方向
1. 针对Gavin Shan的审查意见，Steven Price需要解释或调整代码逻辑（例如可能涉及到版本号比较的边界、错误处理路径等）。
2. 回应Marc Zyngier可能提出的问题（从截断的回复开头推测）；
3. 若有必要，需要在下一个补丁版本中更新实现，比如强化版本检查条件、完善注释，或确保在非KVM使用场景下仍符合早期初始化顺序要求；
4. 可能需要补充更多测试场景，确保在没有KVM配置时RMI探测不影响系统启动。

## 新增补丁
此邮件讨论中未发布新的补丁版本，当前讨论的仍是v14版本。后续可能会基于反馈产生v15版本。

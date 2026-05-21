# arm64: RMI: Provide functions to delegate/undelegate ranges of memory

---

## 更新 - 2026-05-21 17:01 UTC

## 核心话题
本讨论围绕 Linux 内核 ARM64 架构上引入 Realm Management Extension（RME）的补丁 v14 系列中的第 9/44 个补丁展开。该补丁由 Steven Price 提交，目的是为 RMI（Realm Management Interface）提供两组核心函数：`rmi_delegate_range()` 与 `rmi_undelegate_range()`，以及其单页包装 `rmi_delegate_page()` / `rmi_undelegate_page()`。这些函数负责将物理内存“委托”给 Realm Management Monitor（RMM），或将已委托的内存撤销委托。

补丁的核心技术动机在于：RMM 需要完全控制用于 Realm 虚拟机及其自身元数据（如页表、跟踪结构）的物理内存。一旦内存被委托，主机将无法访问，任何访问尝试都会触发 Granule Protection Fault。撤销委托只应在 RMM 不再使用该内存时进行（通常意味着 Linux 已销毁相关 RMM 对象），但补丁描述明确指出，若因编程错误导致撤销委托失败（即 RMM 仍在用），则唯一合理的做法是泄露这些物理页，由调用者自行处理。

从邮件片段中可以看到，补丁 v14 的一个重要变更是将这些函数从 KVM 相关代码中移出，放入更通用的 `arch/arm64/kernel/rmi.c` 中。这样做符合“将 RMM 基础功能从 KVM 解耦”的设计方向，使其他非 KVM 组件（如宿主内核自己的内存管理）也能使用委托机制。函数接口接受物理地址与大小，通过 RMI 指令与 RMM 通信，并内置了对 `RMI_BUSY` 和 `RMI_BLOCKED` 返回状态的重试循环，确保可靠完成操作。

Marc Zyngier 在此补丁上提出了评论，随后 Suzuki K Poulose 进行了回复。尽管邮件后面部分被截断，我们无法看到具体就哪些细节展开了讨论，但可以推测该补丁正处于维护者审查阶段，关注点可能包括错误处理策略、函数放置位置、锁与并发控制，以及委托失败后内存泄露的合理性等。

## 参与讨论人员
- Steven Price (Arm)，补丁原作者
- Marc Zyngier (Arm/Google, ARM64/KVM 维护者)，评论者
- Suzuki K Poulose (Arm)，回复 Marc Zyngier 评论的讨论参与者

## 达成的结论
从当前片段无法判断是否达成共识。邮件被截断，Suzuki 回复的具体内容未知，因此无法确定 Marc 的评论是否被接受，或是否有进一步的修改方案。属于仍在讨论中的状态。

## 下一步改进方向
由于信息不完整，下一步方向可能是：
- 继续完善 `rmi_delegate_range` 与 `rmi_undelegate_range` 的错误处理语义，尤其是撤销失败导致页面泄露后向调用方报告的方式；
- 根据维护者建议调整代码在 `arch/arm64/kernel/rmi.c` 中的具体实现（如是否需要锁、是否需要批量委托接口优化等）；
- 在补丁系列的其他部分（如 KVM 与内存管理集成）确保对这两个新接口的正确引用；
- 等待后续邮件讨论揭示具体要求。

## 新增补丁
本线程为 v14 补丁系列的讨论，未发布新版本补丁。讨论的补丁为 `[PATCH v14 09/44] arm64: RMI: Provide functions to delegate/undelegate ranges of memory`，已将委托/撤销委托接口从 KVM 中分离出来。

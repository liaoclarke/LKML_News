# KVM: arm64: gic-v5: Introduce guest IST alloc and management

---

## 更新 - 2026-05-21 14:52 UTC

## 核心话题
本邮件是“KVM: arm64: gic-v5: Introduce guest IST alloc and management”补丁（v2系列第10个补丁）的提交说明，核心议题是为支持GICv5（ARM的下一代中断控制器）的KVM虚拟化引入客户机中断状态表（Interrupt State Tables, IST）的分配与管理机制。在GICv5架构下，中断状态不再仅由寄存器维护，而是由主机的中断路由服务（IRS）通过内存中的表（IST）来跟踪SPI（共享外设中断）和LPI（局部外设中断）的状态。客户机使用由虚拟机管理程序提供的VMTE（虚拟机表项）来向IRS传递其IST。邮件强调了SPI和LPI不同的内存供给模型：

- **SPI的IST**：从客户机视角看，SPI不应需要客户机显式分配内存，这与物理GICv5中SPI无需预先分配内存的特性保持一致。因此，KVM必须在首次运行客户机之前为其分配一个线性IST（因SPI数量预期较少），并在客户机拆除时负责释放。
- **LPI的IST**：客户机会自行分配LPI IST内存，但KVM不会直接将该内存传递给主机IRS，而是分配一个“影子”LPI IST，并将其通过VMTE交付IRS。由于LPI的数量可能很大，当支持且配置的LPI ID空间需要时，此IST可采用两级表结构。主机同样负责在客户机拆除时释放此内存。
- **门铃域扩展**：该补丁同时扩展了门铃（doorbell）域的功能，使门铃能作为发送命令的管道（类似GICv4支持的ioctl接口）。通过`irq_set_vcpu_affinity()`新增了多个命令，例如：
  - `VMT_L2_MAP`：使第二级VM表有效
  - `VMTE_MAKE_VALID` / `VMTE_MAKE_INVALID`：使单个VMTE（即一个VM）有效或无效
  - `SPI_VIST_MAKE_VALID`：使SPI的IST有效
  - `LPI_VIST_MAKE_VALID` / `LPI_VIST_MAKE_INVALID`：使LPI的IST有效或无效
邮件明确指出这些命令在此阶段尚未连接到主机IRS。最后一句被截断，但明显是在说明有意不提供`SPI_VIST_MAKE_INVALID`命令，原因是SPI IST由KVM全周期管理，无需在运行时无效化。

整个补丁的目标是为GICv5虚拟化搭建基础的内存管理框架，实现客户机中断状态的隔离与高效切换，并为后续将命令实际传递给硬件IRS做好铺垫。

## 参与讨论人员
- Sascha Bischoff (Arm)

由于所提供的邮件仅为补丁提交，无后续回复，因此本线程仅有一位参与者。

## 达成的结论
未在讨论中达成任何结论。该邮件是一个独立的补丁提交，寻求上游社区的审查与合并。目前仅陈述了设计意图和实现方式，无争议或共识记录。

## 下一步改进方向
- 需要社区维护者或其他开发者对该补丁进行技术审查，评估IST分配策略、影子LPI表两级结构的动态扩展逻辑以及门铃命令接口设计的合理性。
- 后续补丁需将本补丁中定义的命令（如`SPI_VIST_MAKE_VALID`等）实际链接到主机IRS硬件操作，完成完整的生命周期管理流程。
- 需要补充说明为何不实现`SPI_VIST_MAKE_INVALID`，并确保该设计在客户机SPI重映射或销毁时由KVM直接处理内存释放是安全且完整的。
- 进行针对不同LPI ID空间大小的压力测试，验证两级IST分配与释放的正确性。

## 新增补丁
- **[PATCH v2 10/39]** KVM: arm64: gic-v5: Introduce guest IST alloc and management （本邮件即为该补丁的v2版本提交，无更新的补丁版本在本线程发布。）

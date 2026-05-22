# [DO NOT MERGE] arm64/coco: Add pKVM as a CC platform

---

## 更新 - 2026-05-22 09:57 UTC

## 核心话题
本邮件是 ARM64 机密计算 (Confidential Computing, CoCo) 系列补丁的第 5 版第 1 个补丁，标题明确标注 `[DO NOT MERGE]`（暂不合并）。补丁的核心内容是将 pKVM (Protected KVM) 作为一个机密计算 (CC) 平台暴露给内核其余部分，主要通过 `cc_platform_has()` 机制实现。pKVM 实际上支持内存加密，但此前未在通用 CC 框架中注册，导致内核无法感知其机密计算特性。  
补丁通过新增辅助函数 `is_protected_kvm_guest()` 来判定当前是否运行在 pKVM 保护的虚拟机实例中，并将该判定整合进设备 DMA 一致性路径——修改 `force_dma_unencrypted()`，使其在 `is_realm_world()` 或 `is_protected_kvm_guest()` 任一为真时返回 `true`。这一改动的原因是：在 pKVM 环境下，所有设备均被模拟，其内存必须通过解密（共享）的方式交还给宿主机，因此需要强制将 DMA 映射视为非加密。  
代码同时调整了 `arch/arm64/include/asm/hypervisor.h`、`arch/arm64/include/asm/mem_encrypt.h`、`arch/arm64/mm/init.c` 以及 `drivers/virt/coco/pkvm-guest/arm-pkvm-guest.c`，将原本仅在 RSI (Realm Service Interface) 中执行的某些初始化逻辑剥离，使 pKVM guest 也能独立设置 CC 平台属性。补丁由 Mostafa Saleh (Google) 编写，Aneesh Kumar K.V (Arm) 签发，属于一个包含 20 个补丁的系列中的第一项，但由于标记了 `[DO NOT MERGE]`，很可能是因为该系列其余部分尚未就绪，或者本补丁仅作为依赖项被提前展示，等待整体架构评审通过后再考虑合并。

## 参与讨论人员
- **Aneesh Kumar K.V** (Arm)，补丁提交者  
- **Mostafa Saleh** (Google)，补丁原作者  

（该线索目前仅出现一封补丁提交邮件，无后续回复或讨论参与者）

## 达成的结论
由于该邮件为单向补丁提交，且标记为 `[DO NOT MERGE]`，邮件列表中尚未出现针对本补丁的评审意见或讨论，因此**未达成任何结论**。本补丁的状态更像是“依赖预展示”或“仅为后续讨论提供上下文”，其最终是否被接纳将取决于整个系列其余部分的评审结果以及相关维护者的反馈。

## 下一步改进方向
- 等待整个 20 补丁系列完整发布，并交由 ARM64 及 KVM/机密计算子系统维护者进行完整评审。  
- 阐明为何本补丁必须单独标记 `[DO NOT MERGE]` —— 可能由于后续补丁会进一步重构 CC 平台逻辑，或者当前实现存在尚未解决的依赖问题。  
- 若该补丁最终需要合并，需提供充分的测试证明，尤其是在 pKVM guest 下 DMA 映射行为的正确性，以及是否会影响非 CC 平台的正常流程。  
- 可能需要补充文档或变更日志，详细说明 pKVM 下内存加密/解密模型与 Realm 世界的异同，以及为何强制 DMA 未加密的前提成立。

## 新增补丁
- **PATCH v5 01/20**：本邮件所附补丁，版本 v5，内容是“Add pKVM as a CC platform”，标注 `[DO NOT MERGE]`。目前未见更高版本或修订版本在同一线索中被提出。

# KVM: arm64: Fix CONFIG_PKVM_DISABLE_STAGE2_ON_PANIC

---

## 更新 - 2026-05-20 23:08 UTC

## 核心话题
本邮件讨论的是一个针对 ARM64 KVM 保护虚拟机（pKVM）实现的修复补丁。问题的根源在于 `arch/arm64/kvm/hyp/nvhe/host.S` 文件中，关于“panic 时禁用宿主 stage-2 页表”的配置宏被错误拼写。宏名称本应为 `CONFIG_PKVM_DISABLE_STAGE2_ON_PANIC`，但代码中漏掉了 `CONFIG_` 前缀，写成了 `PKVM_DISABLE_STAGE2_ON_PANIC`。由于 Kconfig 生成的配置选项通常以 `CONFIG_` 开头，这个拼写错误导致条件编译指令 `#ifdef` 永远无法匹配到正确的配置，因此即使在编译时已启用该功能，在实际 pKVM 异常崩溃（panic）时也无法执行禁用宿主 stage-2 映射的代码路径。

禁用宿主 stage-2 在 pKVM 的 panic 处理中具有重要意义：当 Hyp 模式下的代码遇到致命错误时，保持 stage-2 映射活动可能会使宿主的后续处理（例如内核崩溃转储和堆栈回溯）变得不可靠，因为页表相关限制可能会干扰 EL1 对内存的访问。该补丁引用的上次提交 `9019e82c7e46 ("KVM: arm64: Add PKVM_DISABLE_STAGE2_ON_PANIC")` 正是为了在 panic 时主动清除 HCR_EL2 中的 VM 位（`HCR_VM`），以禁用 stage-2，从而让宿主回溯及其他信息收集更加稳定。由于配置宏的拼写错误，这段清 VM 位的指令从未被编译进内核，导致回溯功能受损，影响了 pKVM 下问题的调试和诊断效率。

修复本身非常简单，仅需在 `host.S` 中添加缺失的 `CONFIG_` 前缀。补丁提交者明确指出这是“typofix”，并给出了 Fixes 标签指向引入该错误的提交。补丁基提交为 `5200f5f493f79f14bbdc349e402a40dfb32f23c8`，说明该问题可能存在于某个当前主线或维护分支中。整体来看，这是一个对编译时选项引用的纯修补，不涉及逻辑或架构层面的调整，但对其所影响的功能而言十分关键，直接关系到 pKVM 环境下 panic 时的可观测性和可靠性。

## 参与讨论人员
- Vincent Donnefort (Google) —— 补丁作者，负责提交修复。

## 达成的结论
本补丁是一封独立的修复邮件，截至分析时未见回复，因此尚未形成多人讨论的共识。由于该错误属于明显的拼写错误，且修复方式清晰、无争议，预计可以顺利通过审查并被采纳。

## 下一步改进方向
- 等待 ARM64 KVM 维护者对补丁进行形式审查和内容确认，之后将其合入相应的分支（通常是 `kvmarm/next` 或 `fixes`）。
- 如果自动化测试或相关开发者有条件，可以在启用了 `CONFIG_PKVM_DISABLE_STAGE2_ON_PANIC` 的内核上触发 pKVM panic 场景，验证禁用 stage-2 的行为是否正确，以及宿主回溯日志是否恢复可靠。
- 检查是否存在其他架构或文件中的类似宏拼写错误，防止同样类型的问题发生。

## 新增补丁
- `[PATCH] KVM: arm64: Fix CONFIG_PKVM_DISABLE_STAGE2_ON_PANIC` (v1)  
  变更：将 `arch/arm64/kvm/hyp/nvhe/host.S` 中的 `#ifdef PKVM_DISABLE_STAGE2_ON_PANIC` 修正为 `#ifdef CONFIG_PKVM_DISABLE_STAGE2_ON_PANIC`，修复因拼写错误导致 panic 时无法禁用宿主 stage-2 的问题。

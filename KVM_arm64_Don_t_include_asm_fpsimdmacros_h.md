# KVM: arm64: Don't include <asm/fpsimdmacros.h>

---

## 更新 - 2026-05-21 14:25 UTC

## 核心话题
该邮件是 Mark Rutland 提交的 18 个补丁系列中的第一封，主题为清理 ARM64 KVM 虚拟机监控器（hyp）入口汇编代码中不必要的头文件依赖。具体来说，补丁删除了 `arch/arm64/kvm/hyp/entry.S` 中对 `<asm/fpsimdmacros.h>` 的包含。

技术动机非常明确：该头文件定义的浮点/ SIMD 相关宏从未被 `hyp/entry.S` 中的任何代码使用过。正如提交说明所指出，“The fpsimd macros have never been used by code in hyp/entry.S, and were instead used by code in hyp/fpsimd.S.” 这表明历史上可能因为代码重构或迁移，原本使用这些宏的代码被移到了 `hyp/fpsimd.S`，但入口文件的包含语句没有被同步清理，形成冗余包含。

移除该包含不会产生任何功能性变化（“There should be no functional change as a result of this patch.”），属于纯粹的代码整洁性改进。这种清理有助于减少编译依赖，缩短编译时间，并降低未来维护者产生困惑的可能性。作为 18 补丁系列的开篇，它很可能为后续更深层的 KVM 或 FPSIMD 状态管理重构做铺垫，确保代码库清晰无误。

## 参与讨论人员
- Mark Rutland (Arm)

## 达成的结论
由于邮件本身只是补丁提交，线程中没有出现任何回复或讨论，因此未形成任何讨论结论。该补丁处于待审状态。

## 下一步改进方向
该补丁需要获得相关维护者（如 Marc Zyngier、Oliver Upton、Will Deacon、Catalin Marinas 等 ARM64 及 KVM 维护者）的 review 和 ack。需验证删除后确实没有隐藏的依赖，并将此补丁作为整个 18 补丁系列的一部分进行合并或进一步修订。维护者可能会要求测试确认无回归。

## 新增补丁
本邮件仅包含补丁系列的 v1 版本，邮件标题为 `[PATCH 01/18] KVM: arm64: Don't include <asm/fpsimdmacros.h>`。未出现后续更新版本。

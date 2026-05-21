# kvm: arm64: Include kvm_emulate.h in kvm/arm_psci.h

---

## 更新 - 2026-05-21 16:11 UTC

## 核心话题
本邮件讨论围绕一个用于修复潜在编译错误的补丁展开。该补丁针对文件 `include/kvm/arm_psci.h`，在其中显式包含了缺失的头文件 `asm/kvm_emulate.h`。修复的动机是，如果 `kvm/arm_psci.h` 在 `kvm_emulate.h` 之后被包含，函数 `kvm_psci_version` 中调用的 `vcpu_has_feature` 会因隐式声明而导致编译失败，具体错误信息如下：
```
./include/kvm/arm_psci.h:29:13: error: implicit declaration of function
   'vcpu_has_feature'; did you mean 'cpu_have_feature'? [-Werror=implicit-function-declaration]
```
补丁本身是 trivial 的修复，已获得 Reviewed-by 标签。然而，KVM/arm64 维护者 Marc Zyngier 在回复中指出，该补丁的标题前缀不符合 KVM/arm64 子系统的统一规范。他说：“Unrelated to this patch, but really easy to fix: the standard prefix for patches targeting KVM/arm64 is: 'KVM: arm64: [opt subsys:] Something starting with a capital letter'”。即标准格式应为 `KVM: arm64:`，其中 `KVM` 需大写，且可选子子系统（如 CCA）作为 `opt subsys`，但在此补丁标题中却使用了小写的 `kvm: arm64:`。Marc 的评论纯粹是关于补丁元数据（标题格式）的一致性，不涉及任何技术内容的争议。Steven Price 随即表示会采纳这个建议，并在下一版提交中进行修改。整个讨论核心是对提交规范的对齐，而非对补丁功能的评审。

## 参与讨论人员
- Marc Zyngier (kernel.org) —— KVM/arm64 维护者，提出了格式统一的要求。
- Steven Price (arm.com) —— 该补丁系列的提交者，负责回应并承诺修改。
- (补丁原始作者：Suzuki K Poulose (arm.com))
- (补丁审查者：Gavin Shan (redhat.com))

## 达成的结论
双方迅速达成共识。Steven Price 完全接受 Marc Zyngier 的建议，同意在下一版补丁中将标题前缀从小写的 `kvm: arm64:` 修改为标准的大写开头格式 `KVM: arm64:`。

## 下一步改进方向
提交者在下一版补丁系列（v15）中，需要将所有相关补丁的标题前缀统一修改为 `KVM: arm64:`，必要时添加可选的子子系统标签（如 `CCA`），以确保符合 KVM/arm64 维护者要求的命名一致性。

## 新增补丁
此邮件线程中未发布新的补丁版本。

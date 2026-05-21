# kvm: arm64: Avoid including linux/kvm_host.h in kvm_pgtable.h

---

## 更新 - 2026-05-21 16:11 UTC

## 核心话题
本邮件讨论的是针对 Linux 内核 ARM64 架构 KVM 代码的一个头文件包含清理补丁。补丁作者 Steven Price 在 v14 版本系列中提交了第 02/44 号补丁，其核心目标是避免在 `arch/arm64/include/asm/kvm_pgtable.h` 中包含 `linux/kvm_host.h`，从而防止将来出现循环包含问题。为了替代被移除的头文件，补丁显式引入了 `linux/kvm_types.h` 和 `linux/rbtree_types.h`，并为仅以指针形式使用的 `struct kvm_s2_mmu` 添加了前向声明。同时，补丁还修复了 `pgtable.c` 和 `kvm_pkvm.h` 此前通过间接包含获得 `kvm_host.h` 的依赖，使它们直接包含该头文件。

维护者 Marc Zyngier 在审核时提出了疑问，对引入 `rbtree_types.h` 感到意外，并询问该头文件的依赖从何而来。Steven Price 解释说 `struct kvm_pgtable` 中包含一个 `struct rb_root_cached` 类型的成员 `pkvm_mappings`（用于 pKVM 映射的红黑树根节点），因此需要该类型定义。他承认这种设计可能不够优雅，但从包含（include）关系的角度看，这是最干净的解决方案。这反映了内核头文件管理中在“避免包含污染”与“结构体成员暴露”之间的权衡：为了避免包含庞大的 `kvm_host.h`，不得不引入更细粒度的类型头文件，但这样做又暴露了页表结构内部使用了红黑树这一实现细节。

## 参与讨论人员
- **Steven Price** (Arm)
- **Marc Zyngier** (Arm Linux 维护者，根据上下文推测)

## 达成的结论
在给出的邮件片断中，双方并未就补丁修改达成最终共识。Steven Price 对 Marc Zyngier 的疑问给出了技术解释，说明了 `rbtree_types.h` 的引入原因。Marc 尚未对这一解释做出进一步回应（该片断仅到 Steven 的解释为止）。因此当前状态为：疑问已澄清，等待维护者基于解释决定是否接受该方式或要求重构。

## 下一步改进方向
- Marc Zyngier 需要基于 Steven 的解释，决定是否接受当前补丁中引入 `rbtree_types.h` 的做法。
- 若不接受，可能需要讨论并重构 `struct kvm_pgtable`，以将 `rb_root_cached` 隐藏在实现内部（如改用指针），从而避免在头文件中暴露该类型需求。
- 若接受，则可继续审核该补丁系列中后续的补丁，并可能将其合并入相关分支。
- 无论哪种情况，都需要确保没有引入新的编译警告或循环包含风险。

## 新增补丁
本邮件讨论的补丁即为 v14 版本系列中的一部分（`[PATCH v14 02/44]`），该邮件本身并未提出新版本补丁，仅是对现有补丁的审核交流。

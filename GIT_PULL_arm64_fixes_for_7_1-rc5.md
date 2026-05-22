# [GIT PULL] arm64 fixes for 7.1-rc5

---

## 更新 - 2026-05-22 14:08 UTC

## 核心话题
该邮件为 ARM64 架构维护者 Catalin Marinas 在 Linux 7.1-rc5 周期向 Linus Torvalds 发起的 GIT PULL 请求，旨在合入两个 arm64 修复补丁。

第一个补丁由 Vladimir Murzin 提交，修复了 ARM64 探针（probes）对带提示（hinted）条件分支指令的处理。某些变体如 `BC.cond` 可与 `B.cond` 指令采用相同方式进行模拟，因此将 `B.cond` 的解码掩码扩展到同时覆盖 `BC.cond`。具体改动位于 `arch/arm64/include/asm/insn.h`，将一条指令的解码掩码位宽从 2 字节调整为 2 字节，实际 diff 显示 `#define AARCH64_INSN_SIZE 4` 等改动，但这里描述为“extend the decode mask”，实际提交修改了 `aarch64_insn_is_bcond` 中的掩码，确保两类指令均能被正确模拟。

第二个补丁由 Zeng Heng 提交，解决了 PMD 表取消共享时 walk cache（页表遍历缓存，即 TLB 中的中间表项缓存）未正确刷新导致的一致性问题。近期 `huge_pmd_unshare()` 重构引入了 `mmu_gather::unshared_tables` 标志，但 arm64 的 TLB 刷新逻辑仍沿用仅针对叶子项（leaf entries）的指令 `TLBI VALE1IS`。当 `tlb->unshared_tables` 置位时，需要改用非叶指令 `TLBI VAE1IS` 以刷新 walk cache，确保页表中间项变更对后续访问可见。修改位于 `arch/arm64/include/asm/tlb.h`。

这两个修复均针对 rc 周期中发现的具体功能问题，缺乏它们可能导致探针工具异常或内存管理缺页/错误访问，因此作为 rc 修复合入是合适的。

## 参与讨论人员
- **Catalin Marinas** (ARM)，ARM64 架构维护者，发送 pull request
- **Vladimir Murzin**，修复 “arm64: probes: Handle probes on hinted conditional branch instructions” 的补丁作者
- **Zeng Heng**，修复 “arm64: tlb: Flush walk cache when unsharing PMD tables” 的补丁作者
- **Linus Torvalds** (Linux 基金会)，主线维护者，pull request 的接收者

## 达成的结论
此线程为单一的 GIT PULL 请求，未包含技术讨论或异议。Catalin Marinas 作为维护者已完成补丁审查，认为它们适合在 rc5 合入。无持续争论，结论是上述两个补丁已准备好进入主线（7.1-rc5），Linus 通常会在数小时内合并该 pull request。

## 下一步改进方向
由于这些是针对性修复，合并后无需额外代码更改。可能的后续步骤：
- 待 Linus 合入后，确保补丁在其余 rc 周期中接受持续测试，尤其是启用了 kprobes/uprobes 的环境以及涉及 THP（透明大页）取消共享的工作负载。
- 如出现回归，可能需要进一步调整 `unshared_tables` 相关逻辑或扩展解码掩码的准确性。

## 新增补丁
此 pull request 中并不包含在讨论过程中重新发布的增量补丁版本，而是直接集成的两个补丁，作为一处变更提交：
- 补丁 1：`arm64: probes: Handle probes on hinted conditional branch instructions`（Vladimir Murzin）
- 补丁 2：`arm64: tlb: Flush walk cache when unsharing PMD tables`（Zeng Heng）

两者均合并在本 pull request 的 git 树中，最终由 Linus 取用。

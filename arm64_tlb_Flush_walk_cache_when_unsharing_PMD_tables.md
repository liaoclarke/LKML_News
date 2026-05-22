# arm64: tlb: Flush walk cache when unsharing PMD tables

---

## 更新 - 2026-05-21 16:15 UTC

## 核心话题
该补丁针对 ARM64 架构下的 TLB 刷新逻辑缺陷，修复了在取消共享 PMD 页表（huge_pmd_unshare）时 walk cache 未正确失效的问题。当 hugetlb 调用 `huge_pmd_unshare` 分离共享的 PMD 表时，通用 mm 层通过 `tlb_unshare_pmd_ptdesc()` 将 `tlb->unshared_tables` 置为 `true`，表明有页表被“取消共享”（而非释放）。然而，ARM64 的 `tlb_flush()` 实现此前只检查了 `tlb->freed_tables` 来决定 TLB 无效化指令的类型：若为 `true` 则使用 `TLBF_NONE`（对应 `VAE1IS`，可使非叶子项和 walk cache 无效），否则使用 `TLBF_NOWALKCACHE`（对应 `VALE1IS`，仅使叶子项无效，不触及 walk cache 和非叶子项）。由于 `unshared_tables` 未被考虑，取消共享时仍会走 `VALE1IS` 路径，导致 PMD 级别的旧页表项可能残留在硬件 walk cache 中，引发后续内存访问使用错误翻译结果，属于严重的一致性问题。

补丁将 `tlb_flush` 中的判断条件修改为 `(tlb->freed_tables || tlb->unshared_tables) ? TLBF_NONE : TLBF_NOWALKCACHE`，确保无论表是被释放还是取消共享，只要页表结构发生了变化，都会使用 `VAE1IS` 彻底清理 walk cache 中可能缓存的中间级描述符。作者还提供了 `VAE1IS` 与 `VALE1IS` 在不同 TTL（Translation Table Level）参数下的精确行为差异表，佐证了修改的正确性。Catalin Marinas 回复确认修复合理，并要求补丁添加 `Fixes` 标签和 `Cc: stable`，以指明该缺陷由提交 `8ce720d5bd91 ("mm/hugetlb: fix excessive IPI broadcasts when unsharing PMD tables using mmu_gather")` 引入，确保合入稳定版。

## 参与讨论人员
- Zeng Heng (zengheng4@huawei.com / zengheng@huaweicloud.com) – 华为，补丁作者
- Catalin Marinas (catalin.marinas@arm.com) – ARM，维护者/评审者
- 另提及抄送 David H.，可能为 David Hildenbrand，但邮件内未出现其回复

## 达成的结论
一致认为该修复是正确且必要的。Catalin Marinas 明确指出 “The fix looks fine”，未提出逻辑异议。共识在于该补丁需要补充 `Fixes` 标签和 `Cc: <stable@vger.kernel.org>` 以向稳定分支回传。至此，技术方案已确定，只需要完成提交信息的规范化。

## 下一步改进方向
- 作者需发布 v2 补丁，补充提交信息：
  - 添加 `Fixes: 8ce720d5bd91 ("mm/hugetlb: fix excessive IPI broadcasts when unsharing PMD tables using mmu_gather")`
  - 添加 `Cc: <stable@vger.kernel.org>`
- 可能需要等待可能被抄送的 David Hildenbrand 等人的进一步 ack 或 review，但主要技术审核已完成。
- 合并后需关注稳定分支的适配，确保该修复后向移植无误。

## 新增补丁
本线程中目前仅出现初始补丁（v1），尚无根据反馈修改后的新版本。预期下一版为 v2，主要变动为补充 Fixes 和 Cc stable 标签，代码逻辑本身不变。

---

## 更新 - 2026-05-22 11:13 UTC

## 核心话题
该邮件讨论的是针对 ARM64 架构 `TLB` 刷新时 walk cache 失效不完整的一个修复补丁。补丁作者曾恒（Zeng Heng）指出，当通过 `huge_pmd_unshare()` 取消共享 PMD 页表时，`tlb_unshare_pmd_ptdesc()` 会将 `tlb->unshared_tables` 设置为 `true`，但 ARM64 的 `tlb_flush()` 函数仅检查了 `tlb->freed_tables` 来决定使用的 TLB 失效指令类型：若存在被释放的页表，则使用 `TLBF_NONE`（底层对应 `VAE1IS` 指令，会连带刷新 walk cache 中的非叶子条目），否则使用 `TLBF_NOWALKCACHE`（底层对应 `VALE1IS`，仅刷新叶子条目，不触及 walk cache）。这种检查遗漏导致取消共享后旧的 PMD 条目仍可能残留在 walk cache 中，后续页表遍历可能读到过期条目，引发难以预料的错误。

补丁的修改非常简单，就是在 `arch/arm64/include/asm/tlb.h` 中增加对 `tlb->unshared_tables` 的判断，使得当 `unshared_tables` 或 `freed_tables` 任一为真时，均采用 `TLBF_NONE` 以完整刷新 walk cache。补丁中还附上了一张清晰的指令组合与实际失效范围对照表，用来区分 `VAE1IS` 与 `VALE1IS` 在不同 TTL 参数下的行为，佐证了修复的必要性。

Catalin Marinas 审阅后认为修改本身是合理的，但他指出补丁缺少 `Fixes:` 标签和 `Cc: stable` 标记。该问题是由提交 `8ce720d5bd91 ("mm/hugetlb: fix excessive IPI broadcasts when unsharing PMD tables using mmu_gather")` 引入的，且对稳定内核同样存在，因此应当补上这些元信息，以便正确回溯和合入稳定分支。

## 参与讨论人员
- Catalin Marinas <catalin.marinas@arm.com>（Arm）
- Zeng Heng（曾恒）<zengheng4@huawei.com>（华为）

## 达成的结论
Catalin Marinas 对补丁的技术方案表示认可（“The fix looks fine”），但明确提出需要补充 `Fixes:` 和 `Cc: stable` 标签。这可以视为一种有条件接受 —— 作者需要根据评审意见修正提交信息后重新发送补丁。尚未形成最终合入的结论，因为补丁尚未更新并重新发布。

## 下一步改进方向
1. 补丁作者需要在提交信息中添加一行 `Fixes: 8ce720d5bd91 ("mm/hugetlb: fix excessive IPI broadcasts when unsharing PMD tables using mmu_gather")`。
2. 同时在签名区之前加入 `Cc: <stable@vger.kernel.org>`，以便稳定内核维护者知悉该修复需要回移植。
3. 重新发送补丁的 v2 版本，并适当在 changelog 中说明新增的标签。补丁代码本身无需修改。

## 新增补丁
本邮件线程中**未出现新版本补丁**，仅有原始补丁以及 Catalin 的 Review 回复。补丁作者下一步应发布 v2。

---

## 更新 - 2026-05-22 11:38 UTC

## 核心话题
本讨论源自 Zeng Heng 提交的一个补丁，旨在修复 ARM64 架构下 TLBI（TLB Invalidate）操作在 PMD 表解除共享（unshare）时未正确清理 walk cache 的问题。

在 Linux 内核中，当通过 `huge_pmd_unshare()` 解除一个 PMD 级别页表的共享时，需要确保 CPU 的页表 walk cache 中对应的陈旧条目被无效化，否则后续的页表遍历可能会读到错误的中间级页表项。现有的 tlbi 冲刷逻辑中，`tlb_unshare_pmd_ptdesc()` 函数会将 `tlb->unshared_tables` 设置为 `true`，但是 arm64 架构的 `tlb_flush()` 实现只检查了 `tlb->freed_tables` 来决定使用哪种 TLB 无效化指令。若仅释放了页表（`freed_tables` 为真），会使用完整的 `vae1is`（带或不带 TTL）来同时清理 walk cache 和叶子条目；否则默认使用 `vale1is`（仅无效化叶子，不清理非叶子缓存），导致在 only-unshare 的场景下，陈旧的 PMD 表项仍然留在 walk cache 中，可能引发页表遍历错误。

Zeng Heng 的修复思路是让条件判断同时考虑 `unshared_tables`，当该标志为真时同样采用能够清理 walk cache 的指令组合（`vae1is`）。邮件中详细区分了两种指令的行为：
- `VAE1IS` 配合适当的翻译表级别（TTL）可无效化所有级别或指定级别的非叶子与叶子条目，即完整清理 walk cache。
- `VALE1IS` 仅无效化叶子条目，不会清理非叶子缓存。

Catalin Marinas 在回复中进一步探讨了指令组合的具体影响，并提出是否应该根据实际的无效化范围选择更精确的 TTL 来使用 `VAE1IS`，而不仅仅在 `freed_tables` 或 `unshared_tables` 为真时退回到全范围无效化。技术争论点在于：是直接使用 `VAE1IS` + TTL=0（全范围）更安全，还是尽可能指定明确的级别（如 L2）以减少性能开销，同时保证正确性。由于邮件截断，无法得知双方是否在指令粒度和 TTL 选择上达成完全一致，但核心问题（缺少 walk cache 刷新）已被明确指出，补丁的逻辑方向基本正确。

## 参与讨论人员
- **Zeng Heng**（华为），补丁提交者，报告并分析了问题。
- **Catalin Marinas**（Arm），arm64 维护者，审核补丁并深入探讨指令使用细节。

## 达成的结论
讨论中已明确现有代码存在缺陷，即 `tlb_flush()` 对 `unshared_tables` 的忽略会导致 walk cache 残留，必须修复。但针对修复的具体方式——是简单地将 `unshared_tables` 加入条件，还是同时优化指令选择（如针对性地使用 `VAE1IS` + 合适的 TTL）——尚未看到最终定论。考虑到邮件末尾被截断，可以认为补丁的大方向已获认同，但可能在指令组合的精细度上仍有不同意见，尚未形成最终补丁版本。

## 下一步改进方向
1. Zeng Heng 需要根据 Catalin 的反馈调整补丁，明确在 `freed_tables` 或 `unshared_tables` 为真时，具体应使用何种 TLBI 指令及 TTL 值；可能需要区分是单纯 PMD unshare 还是同时涉及 free，以采用最优的无效化范围。
2. 在修改后补充更详尽的提交说明，解释为何选择特定的指令组合，并引用 ARM 架构手册的相关章节。
3. 增加相应的测试用例或测试记录，特别是在多核环境下验证 hugepage unshare 后不再出现错误遍历。
4. 等待 arm64 维护者的进一步评审，确认对性能与正确性没有负面影响。

## 新增补丁
本线索中仅出现初始补丁 `[PATCH] arm64: tlb: Flush walk cache when unsharing PMD tables`，尚未发布新的版本（如 v2）。预计在回应评审意见后会有新版本补丁提交。

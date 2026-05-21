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

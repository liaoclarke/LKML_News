# btrfs: require at least 4 devices for RAID 6

---

## 更新 - 2026-05-22 09:57 UTC

## 核心话题
本邮件线程讨论 Btrfs 的 RAID5/6 清理工作中的一项具体修改：对 RAID6 强制要求至少 4 个块设备。原始作者 H. Peter Anvin 指出，Linux 内核的 RAID-6 代码从一开始就未支持仅为 3 个单元的退化情况，过去若能工作纯属偶然，且这种配置可能导致内核崩溃或页缓存损坏。因此 Christoph Hellwig 原本想在清理系列中加入一个补丁来排除 3 设备 RAID6 的配置，但遭到反对。

关键引述：
- H. Peter Anvin：“The RAID-6 code has *never* supported only 3 units... the degenerate case (3) would have required extra trays in the code to no user benefit. I would not be surprised if the kernel crashed or corrupted the page cache in that case.”
- Christoph Hellwig 随后表示：“for the about to be resent version I'll drop this btrfs patch over the stated objection... users of this configuration will get a WARN_ON_ONCE triggered, but otherwise keep working... as before.”
- Qu Wenruo 提出替代方案：“For the btrfs part, I believe I can get the current 2-disk-raid5 and 3-disk-raid6 to fallback to raid1 inside btrfs.”

因此讨论的核心转向：不通过块层硬性禁止 3 盘 RAID6，而是由 Btrfs 自身识别这些不安全的配置，并在文件系统内部将其透明降级为 RAID1，以保护用户数据。同时需要协调该修复的合并时间，以配合 RAID5/6 清理系列在 7.2-rc1 窗口的合入。

## 参与讨论人员
- Qu Wenruo (wqu@suse.com, quwenruo.btrfs@gmx.com) — Btrfs 开发者
- Andrew Morton (akpm@linux-foundation.org) — 内核维护者
- H. Peter Anvin — RAID-6 代码原始作者
- Christoph Hellwig — 清理系列的提交者

## 达成的结论
尚未完全达成最终补丁形态的共识，但形成了明确的技术方向：
- 放弃在块层或通用 RAID 代码中强制拒绝 3 设备 RAID6 的做法。
- 保留 WARN_ON_ONCE 作为警示，但不主动阻止挂载或导致崩溃。
- 转由 Btrfs 内部实现降级逻辑：当检测到 2 盘 RAID5 或 3 盘 RAID6 时，自动降级为 RAID1，从而彻底避免数据风险。
- 合并窗口方面，RAID5/6 清理系列目标为 7.2-rc1，Btrfs 开发者认为其降级修复补丁量小，有望同期进入。

## 下一步改进方向
1. Btrfs 降级补丁需要充分审查，以确保降级过程安全、透明且不影响性能。
2. 明确降级策略：是在挂载时自动转换已有数据布局，还是仅对新写入实施 RAID1 模式？
3. 测试：需验证从 3 盘 RAID6 配置迁移到 RAID1 降级后的行为，包括已有数据的读写和 scrubbing。
4. 文档和用户提示：应通过内核日志或用户空间工具明确告知用户配置已降级及风险。
5. 协调合入时间，确保 Btrfs 修复与块层清理系列在相同合并窗口就位，避免出现中间版本存在已知风险窗口。

## 新增补丁
在邮件中 Qu Wenruo 引用了其正在开发的 Btrfs 降级修复补丁链接：
- [补丁 v?] btrfs: fallback to raid1 for 2-device raid5 and 3-device raid6  
  链接：https://lore.kernel.org/linux-btrfs/a1d63733465229936351804f3760803d5894a962.1779274630.git.wqu@suse.com/T/#u  
  该补丁尚未标记版本号，其核心变更是在 Btrfs 中检测到不安全的 RAID5/6 设备数时，强制将配置文件视为 RAID1 处理。

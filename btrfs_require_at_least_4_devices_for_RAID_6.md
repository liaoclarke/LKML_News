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

---

## 更新 - 2026-05-21 17:17 UTC

## 核心话题
本邮件讨论的焦点并非 ARM64 架构，而是关于 btrfs 文件系统中 RAID 6 卷所需的最少设备数量的限制。最初，Andre Morton 的补丁系列（编号 01/19）试图要求 btrfs 的 RAID 6 至少需要 4 个块设备才能创建或运行。这一要求源于 RAID-6 算法的内在规定：RAID-6 需要至少 4 个单元（数据块与校验块之和）才能正常工作。讨论中，H. Peter Anvin（RAID-6 代码的原作者）明确指出，RAID-6 代码从未支持过 3 个设备的情况，任何在 3 个设备上成功运行 RAID-6 的现象都纯属意外，甚至可能导致内核崩溃或页缓存损坏。他坚决主张对此类配置直接报错，以保护用户数据。Christoph Hellwig 一度想通过补丁将这种配置排除在外，但在听到 Peter Anvin 的强烈反对后，决定在即将重新发送的系列中删除这一针对 btrfs 的补丁，改为维持现有行为，并在检测到不支持配置时仅触发 WARN_ON_ONCE 警告。btrfs 的维护者 Qu Wenruo 随后提出，可以在 btrfs 内部将不符合要求的 RAID 配置（如 2 设备的 RAID5 或 3 设备的 RAID6）自动降级为 RAID1，以防止数据丢失，并希望该方案能在下一个合并窗口完成。Andrew Morton 确认该 RAID5/6 代码清理系列的合并目标是 7.2-rc1 合并窗口，并询问时间是否合适。因此，整个讨论围绕着如何在 btrfs 层面优雅地处理底层 RAID 算法不支持的不安全配置，同时推进 RAID5/6 代码的整体清理工作。

## 参与讨论人员
- Andrew Morton (akpm@linux-foundation.org) — Linux 内核维护者  
- Qu Wenruo (quwenruo.btrfs@gmx.com) — btrfs 文件系统开发者/维护者  
- Christoph Hellwig — 存储子系统开发者  
- H. Peter Anvin — RAID-6 代码原作者  

## 达成的结论
达成了一定的共识。Christoph Hellwig 明确表示，出于 H. Peter Anvin 的强烈反对，他将在重新提交的补丁系列中移除那项要求 btrfs RAID 6 至少 4 个设备的补丁，即保留 btrfs 的现有行为不变，但会添加 WARN_ON_ONCE 警告。这相当于承认直接拒绝配置是合理的，但暂时不在当前补丁里强制修改 btrfs。Qu Wenruo 的降级方案（fallback 到 RAID1）被提出作为后续更完善的替代方案，未遭到反对，但尚未落地，需要后续开发。

## 下一步改进方向
- Qu Wenruo 需要实现 btrfs 内部对低设备数 RAID 配置的自动降级功能：将 2 设备的 RAID5 和 3 设备的 RAID6 降级为 RAID1，以安全地防止用户数据丢失。  
- 该 btrfs 改进应尽可能在 Linux 7.2-rc1 合并窗口前完成，以便配合整体的 RAID5/6 清理系列。如果来不及，可能需要后续版本引入。  
- Christoph Hellwig 将重新发送不含争议 btrfs 补丁的 RAID5/6 清理系列，并确保现有不支持的配置仅产生警告，不改变其原有的（可能崩溃的）行为，等待 btrfs 侧的正确修复。

## 新增补丁
在本讨论线程中未直接提交新的补丁版本。Christoph Hellwig 表示将重新发送整个系列（可能为 v2 或更新的版本），且该版本将移除原先的“btrfs: require at least 4 devices for RAID 6”补丁。该新版本补丁集尚未在邮件中直接贴出，但明确将在未来发布。因此，该线程内无可列出的新补丁版本号。

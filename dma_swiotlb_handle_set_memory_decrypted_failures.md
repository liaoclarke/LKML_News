# dma: swiotlb: handle set_memory_decrypted() failures

---

## 更新 - 2026-05-22 09:58 UTC

## 核心话题
本补丁旨在解决 swiotlb 子系统中调用 `set_memory_decrypted()` 转换内存加密属性时缺乏错误处理的问题。在机密计算（如 ARM64 CCA、TDX、SEV 等场景）下，swiotlb 缓冲池需要动态地在加密与解密状态之间切换，以便设备进行 DMA 操作。此前代码忽略 `set_memory_decrypted()` 的返回值，一旦解密失败（例如由于硬件或页表限制），swiotlb 仍会继续使用该内存区域，但其实际加密状态与池的元数据（`pool->unencrypted`）不一致。这会导致回弹缓冲区返回的物理页面处于不确定的加密状态，进而可能造成数据泄漏或设备无法正确访问内存。

补丁作者 Aneesh Kumar K.V 提出了分层错误处理策略：
1. 对于默认 swiotlb 池在早期初始化完成后（`swiotlb_update_mem_attributes()` 中），若解密失败，调用新增的 `swiotlb_mark_pool_used()` 将池的所有区域标记为已占用，使其后续无法再分配新的 bounce buffer，从而避免使用不安全的内存。
2. 在延迟初始化路径中，将 `set_memory_decrypted()` 的错误向上传播，让调用者直接处理失败。
3. 对于受限 DMA 池（restricted DMA pools），若预留池无法解密，则直接使设备初始化失败，阻断不可靠的设备操作。

补丁通过引入 `swiotlb_mark_pool_used()` 函数，遍历池的所有区域和槽位，将 `index`、`used`、`list`、`orig_addr` 等元数据重置，并标记所有槽位为非空闲状态，物理地址设为无效值。这样的处理防止了 swiotlb 在解密失败后继续向错误属性的内存分配缓冲区，也避免了在释放池时将处于未知加密状态的页面归还给内存分配器。邮件中给出的代码片段展示了这一函数的实现以及 `swiotlb_update_mem_attributes()` 中对 `set_memory_decrypted()` 返回值的检查与上述标记逻辑。

这一改进增强了 swiotlb 在特殊安全环境下的健壮性，确保内存加密状态与软件元数据严格匹配，属于机密计算基础设施的必要加固。

## 参与讨论人员
- Aneesh Kumar K.V (Arm) <aneesh.kumar@kernel.org>

## 达成的结论
本邮件仅为补丁提交（[PATCH v5 18/20]），邮件列表中未出现任何回复或讨论内容，因此尚未形成任何共识或结论，有待社区审查和反馈。

## 下一步改进方向
- 需要获得相关维护者（如 swiotlb、DMA 映射子系统的维护者）以及密码内存管理领域的开发者审查。
- 可能需要讨论针对早期初始化解密失败的处理方式：当前方案是静默标记池已用，是否应当增加内核警告，或甚至触发 BUG/WARN 以引起开发者注意，需要权衡。
- 需验证该补丁在 x86（含 TDX/SEV）及 ARM64 CCA 环境下的测试覆盖，确保各种错误路径行为符合预期。
- 确认 `swiotlb_mark_pool_used()` 是否足以应对所有竞态条件，以及是否有其他调用 `set_memory_decrypted()` 的位置也需要类似处理。
- 后续可能根据审查意见调整代码结构或报错策略。

## 新增补丁
当前邮件仅包含该补丁的 v5 版本，无更新的补丁版本发布。本补丁为系列 “v5” 中的第 18/20 个，若未来有 v6 版本应在此线程或新线程中发布。

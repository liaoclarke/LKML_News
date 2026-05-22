# mm/vmalloc: Speed up ioremap, vmalloc and vmap with contiguous memory

---

## 更新 - 2026-05-22 13:31 UTC

## 核心话题
该邮件线程由一封补丁集提交邮件组成，主题为“加速连续物理内存场景下 ioremap、vmalloc 和 vmap 的操作”。作者 Wen Jiang（小米）提出一套针对 ARM64 架构的优化方案，目标是在映射的物理内存为完全或部分连续时，大幅提升 ioremap、vmalloc 和 vmap 的性能。技术核心包括两点：1) 当设置多个内存段的 PTE/PMD 时避免重复的页表遍历；2) 在 vmalloc 层和 ARM64 架构层尽可能使用批量映射。

补丁集由 6 个补丁组成，逐步实现以下改进：
- 补丁 1-2 扩展了 ARM64 的 vmalloc CONT-PTE 映射支持，使其能够覆盖多个 CONT-PTE 区域，而不再局限于单个区域。
- 补丁 3 提取了通用辅助函数 `vmap_set_ptes()`，统一 ioremap 与 vmalloc/vmap 路径中的 PTE 映射逻辑，能够处理 CONT_PTE 和常规 PTE 映射，为后续优化做准备。
- 补丁 4 扩展页表遍历路径，使其支持除 PAGE_SHIFT 之外的其他页大小，并消除了大页 vmalloc 映射时的重复页表遍历，相关函数从 `vmap_small_pages_range_noflush()` 重命名为 `vmap_pages_range_noflush_walk()`。
- 补丁 5-6 为物理连续页添加了巨页 vmap 支持，包括对非复合页的 pfn 对齐验证，并支持使用 PMD 映射和 CONT-PTE 映射，这在当前内核的 vmap 中是不支持的。

作者提供了在 RK3588 8 核 ARM64 SoC 上的性能数据：ioremap(1MB) 提速 1.35 倍，vmalloc(1MB) 映射延时（不含分配）在启用 VM_ALLOW_HUGE_VMAP 的前提下提速 1.42 倍，而使用 order-8 页面的 vmap(100MB) 操作更是提速 8.3 倍。该补丁集由 Xueyuan Chen 在 RK3588 平台上协助测试。

版本 v3 相比 v2 的改动包括：使用 `__fls` 替代 `fls`、增加 WARN_ON 检查、修复 `flush_cache_vmap` 的 addr 使用错误、重命名 `__vmap_huge()` 为 `vmap_batched()` 等。该邮件因截断未展示全部内容，但明显是作者独立提交的补丁集，没有出现其他讨论者的回复。

## 参与讨论人员
- Wen Jiang (jiangwen6@xiaomi.com) —— 补丁作者
- Xueyuan Chen —— 测试协助（仅在致谢中提及，未直接参与讨论）

## 达成的结论
该线程中未发生讨论，仅为作者提交的 v3 版补丁集。因此没有形成明确的结论或共识。

## 下一步改进方向
由于没有其他维护者或开发者的评审意见，下一步需要社区对该补丁集进行技术审查，重点关注以下方向：
- 架构维护者（ARM64）对 CONT-PTE 多区域扩展的认可与检查。
- 内存管理（mm）子系统维护者对 `vmap_set_ptes()` 统一接口及巨页 vmap 路径的合理性、安全性审查。
- 需要更多硬件平台的测试报告，特别是是否引入性能退化或稳定性问题。
- 补丁截断处的后续内容需补充完整，例如对批量映射接口的错误处理、锁语义等细节需要明确。
- 代码风格、命名和文档方面可能需要根据社区反馈进行调整。

## 新增补丁
- [PATCH v3 0/6] mm/vmalloc: Speed up ioremap, vmalloc and vmap with contiguous memory（版本 v3）
  主要变更：使用 `__fls` 替代 `fls`、增加 WARN_ON 检查、修复 flush 函数中的地址错误、重命名 `__vmap_huge()` 为 `vmap_batched()`、其余修改因邮件截断未显示。

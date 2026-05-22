# mm/vmalloc: map contiguous pages in batches for vmap() if possible

---

## 更新 - 2026-05-22 13:31 UTC

## 核心话题
本补丁旨在优化内核 `vmap()` 函数在映射物理连续页面时的性能，特别是当传入的页面数组包含高阶（high-order）分配块时。当前 `vmap()` 的实现对每一个页面单独建立页表映射，即便多个页面在物理上连续且属于同一个高阶分配（例如 order-8、order-4 的块），也依然逐个调用映射函数。这导致不必要的页表遍历开销，并且错失了使用大页（huge page）映射以减少 TLB 压力、提升内存访问效率的机会。

补丁描述中明确指出：“In many cases, the pages passed to vmap() may include high-order pages. For example, the systemheap often allocates pages in descending order: order 8, then 4, then 0.” 这一现实场景源于某些内存分配器（如系统堆）倾向于按降序尝试分配高阶块，当高阶分配失败时才回退到 order-0。原生的 `vmap()` 无法发现这些物理连续块，只能以单个页为单位进行映射。

补丁通过引入 `num_pages_contiguous()` 扫描页面数组，识别出物理上连续的一组页面，并计算这批页面所能支持的最大映射阶数（order）。若连续页数大于 1，且体系结构支持可变大小的 vmap 映射（`CONFIG_HAVE_ARCH_HUGE_VMAP` 开启，`ioremap_max_page_shift` 大于 PAGE_SHIFT），则通过 `arch_vmap_pte_supported_map_size()` 检查是否允许该阶数的映射，并在满足第一个页的 pfn 对齐要求时，使用 `vmap_pages_range_noflush_walk()` 一次性建立整个连续块的映射，避免每次映射一小块都重新遍历页表顶层。

值得注意的一个优化点是，补丁假设用户分配内存时采用降序尝试，一旦遇到 order-0 的页面，后续页面也很可能都是 order-0，因此停止继续扫描连续的物理页，从而避免不必要的 `num_pages_contiguous()` 调用。如补丁描述所述：“once an order-0 page is encountered, we stop scanning for contiguous pages since subsequent pages are likely order-0 as well.” 这种启发式方法在常见分配模式下能减少扫描开销，同时不影响正确性。

此改动属于 ARM64 架构上 vmalloc 优化系列的一部分，利用架构提供的 huge vmap 能力，显著减少内核虚拟地址映射的 TLB 条目数量，对诸如 DRM、网络缓冲区等频繁使用 vmap 的子系统有明显性能提升。

## 参与讨论人员
- **Wen Jiang**：邮件发送者，负责发送补丁（`jiangwenxiaomi@gmail.com` / `jiangwen6@xiaomi.com`），代表小米团队。
- **Barry Song (Xiaomi)**：补丁主作者，来自小米（`baohua@kernel.org`）。
- **Dev Jain**：共同开发者，来自 ARM 公司（`dev.jain@arm.com`）。
- **Xueyuan Chen**：负责补丁测试工作（`xueyuan.chen21@gmail.com`）。

由于邮件只包含补丁提交，截至本分析时**没有出现其他讨论者的回复**，因此仅能列出上述参与者。

## 达成的结论
该邮件仅为一个补丁的 v3 版本提交，**尚未收到任何评论或反馈**，因此该线程**未达成任何共识或结论**。补丁处于等待社区审核的状态，技术方案的合理性、性能收益以及潜在的边界条件处理仍有待其他内核开发者评审。

## 下一步改进方向
补丁处于待审核状态，下一步需要完成以下事项：
- **社区评审**：需要 ARM64 架构维护者、mm/vmalloc 维护者审阅代码，确认其正确性与适用场景。
- **性能数据补充**：提供更全面的基准测试结果，展示不同负载下的 TLB miss 降低幅度和实际吞吐提升，以支撑优化合入。
- **边界条件验证**：评审者可能要求对 `num_pages_contiguous()` 和 stop-on-order0 启发式的正确性进行更严格论证，确保在非降序分配或混合 order 场景下不会产生错误映射。
- **代码细节调整**：根据评审意见修正格式、注释或逻辑；可能需增加对额外架构回调的引用，或者对扫描逻辑做进一步抽象。
- **测试计划**：扩大测试覆盖范围，包括不同内存大小、不同分配器行为下的稳定性测试。

## 新增补丁
本邮件是 **v3 版本** 补丁系列中的第 5 个补丁（`[PATCH v3 5/6]`）。线程中提交的补丁版本号为 **v3**，其相比于 v2 的具体变更未在邮件中说明，但从邮件中的 `Co-developed-by` 等 tag 可看出此版本新增了 ARM 公司的 `Dev Jain` 作为联合开发者，可能包含对 ARM 平台 huge vmap 支持的适配改进。此后暂无更新的补丁版本（如 v4）出现在该线程中。

# KVM: arm64: Alloc simple_buffer_page using pKVM hyp allocator

---

## 更新 - 2026-05-20 16:26 UTC

## 核心话题
本补丁是 KVM ARM64 pKVM (protected KVM) 模式下一系列改进中的一部分（17/17），核心目的在于将追踪子系统中的简单环形缓冲区（simple_ring_buffer）备用页面（backing page）的分配方式，从**主机捐赠静态内存** 转移到**由 pKVM 自身的 hypervisor 堆分配器动态分配**。修改之前，主机需要预先分配一块连续的物理内存，并通过 donate 机制交给 hypervisor 用作 trace buffer 的 backing store；现在 hypervisor 通过新引入的 `pKVM hyp allocator` 直接在受保护的地址空间中动态分配。

补丁中明确说明：“Previously, the host allocated and donated a contiguous backing memory for these structures. In pKVM the hypervisor can now allocate them dynamically.” 这意味着 pKVM 的安全性得到加强，减少了宿主对 hypervisor 内部数据布局的控制，也避免了因预先分配不足导致的缓冲区受限问题。此外，补丁提到通过 `pkvm_call_hyp_req()` 包装器调用 `__tracing_load`。该包装器能够在 hypervisor 在分配过程中耗尽堆内存时，自动向主机发起 top-up 请求，获得更多内存再加入 hyp 堆，从而保证分配的弹性，不会因为分配失败而中断 trace 加载流程。

代码变更的另一个关键点是在 `handle___tracing_load` 中，原先直接将 `__tracing_load` 的返回值写入 CPU 寄存器，现在改为使用 `errno_to_smccc()` 将结果按 SMCCC 标准转换，以统一错误处理。同时在 `trace.c` 内部，原来的 `hyp_trace_buffer_load_bpage_backing` 函数被重构为 `hyp_trace_buffer_alloc_bpages`，并加入对 `<nvhe/alloc.h>` 的引用，表明开始使用 hyp 内部的专用分配器。这些改动是在 pKVM 整体启用 hyp 自主内存管理的大背景下进行的，意图让 hypervisor 尽可能自给自足，减少主机对其运行时的干预，进一步提升隔离性和系统韧性。

## 参与讨论人员
- Vincent Donnefort (vdonnefort@google.com)，补丁提交者。

（该线程目前仅包含补丁提交邮件，无其他参与者回复。）

## 达成的结论
本邮件为单一补丁提交，未在讨论中产生明确的共识或反对意见。补丁是否被接受需等待后续审查和社区反馈。目前尚未形成结论。

## 下一步改进方向
1. 需要获得 ARM64 KVM 维护者及社区对该系列补丁的审查，确认 pKVM hyp 分配器设计合理且性能开销可接受。
2. 验证在 hyp 堆耗尽时 `pkvm_call_hyp_req` 能够可靠触发 top-up 并恢复分配，防止死锁或内存泄漏。
3. 确保在 protected 模式下 tracing 功能的完整性，包括卸载 trace buffer 时的内存释放路径是否与新分配器配合良好。
4. 整个系列（17 个补丁）需要整体测试，特别是与 pKVM 相关的内存保护、宿主与 hypervisor 交互等场景。

## 新增补丁
本邮件为 `[PATCH 17/17] KVM: arm64: Alloc simple_buffer_page using pKVM hyp allocator` 的原始提交，本线程内未出现新的修订版本。

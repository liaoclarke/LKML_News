# KVM: arm64: Add topup interface for the pKVM heap allocator

---

## 更新 - 2026-05-20 16:26 UTC

## 核心话题
本邮件是 Vincent Donnefort 为 pKVM（protected KVM，受保护的内核虚拟化）堆分配器添加补充（topup）接口的补丁提交，属于 17 补丁系列中的第 6 个。该补丁旨在解决 pKVM 受保护虚拟机运行过程中，hypervisor（hypervisor）端分配器可能出现内存不足的问题。

技术背景是 pKVM 实现了一种受保护的虚拟化环境，其中 hypervisor 运行在独立的受保护上下文（protected context）中，无法像传统 KVM 那样直接访问主机的内存管理接口。当 hypervisor 需要为受保护虚拟机分配内存时，如果没有足够的空闲页面，可能会面临分配失败的情况。为此，补丁引入了从主机（host）主动向 hypervisor（hypervisor）补充堆内存的机制。

具体实现方面，补丁引入了一个新的 HVC 调用接口和对应的主机端辅助函数。核心实现包括：
1. 新增枚举 `pkvm_topup_id`，其中目前定义了 `PKVM_TOPUP_HYP_ALLOC` 成员，用于标识要对 hyp 分配器进行补充。
2. 在 hypervisor 端实现处理函数 `handle___pkvm_hyp_topup`，该函数通过主机上下文寄存器接收三个参数：`id`（标识要补充哪个分配器）、`head`（物理地址，指向要提供给 hypervisor 的页面列表头部）、`nr_pages`（要补充的页面数量）。处理函数将这些页面通过 `kvm_hyp_memcache` 结构体传递给 hypervisor。
3. 在主机端的 ARM64 KVM 特定头文件 `kvm_asm.h` 中添加了 HVC 调用号 `__KVM_HOST_SMCCC_FUNC___pkvm_hyp_topup`，使主机能够调用该 hypervisor 服务。
4. 在 `kvm_pkvm.h` 公共头文件中声明了 `pkvm_topup_id` 枚举，使得主机和 hypervisor 代码都能理解补充请求的目标分配器类型。

补丁的设计思路是建立一个受控的内存流通通道（memcache），允许主机在 hypervisor 分配器即将耗尽时预先或按需提供内存补充，既保证了内存分配的可靠性，又维护了 pKVM 安全隔离的特性。这为后续补丁中将内存分配与受保护虚拟机生命周期管理解耦奠定了基础。

## 参与讨论人员
Vincent Donnefort（Google） - 补丁提交者

## 达成的结论
本邮件是独立的补丁提交（PATCH 06/17），线程中未出现其他参与者的回复或讨论，因此未能形成讨论结论，也无法确定是否存在共识。补丁本身代表提交者对 pKVM 堆分配器需要 topup 接口的技术主张。

## 下一步改进方向
由于没有收到讨论反馈，后续可能的改进方向包括：
1. **错误处理与返回值检查**：需要明确当 `nr_pages` 为零或物理地址无效时 hypervisor 的处理逻辑，确保接口的健壮性。
2. **内存来源验证**：需要加强主机在调用 topup 前对所提供物理页面的所有权和合法性的验证，防止恶意或错误的页面注入破坏 pKVM 隔离。
3. **补充策略实施**：需要在主机端实现智能的 topup 调用策略（例如基于 watermarks 触发），这可能在系列的后续补丁中完成。
4. **多分配器支持扩展**：枚举 `pkvm_topup_id` 目前只有一个成员，未来可能需要扩展支持其他 hypervisor 内部分配器的补充。
5. **性能考量**：评估通过 HVC 批量传输页面对延迟的影响，考虑是否需要异步接口或预填充机制。

## 新增补丁
本邮件包含的是 [PATCH 06/17] 的初始版本（无版本号变更）。其补丁内容摘要：
- 在 `kvm_asm.h` 中新增 HVC 函数 ID `__KVM_HOST_SMCCC_FUNC___pkvm_hyp_topup`
- 在 `kvm_pkvm.h` 中新增枚举 `pkvm_topup_id`，包含 `PKVM_TOPUP_HYP_ALLOC`
- 在 `hyp-main.c` 中实现 HVC 处理函数，从主机上下文寄存器解析参数并通过 memcache 交给 hypervisor 分配器

# [RFC PATCH 2/2] arm64: mm: add SMCCC-backed cache invalidate provider

---

## 更新 - 2026-05-21 15:12 UTC

## 核心话题
该邮件讨论的是为 ARM64 架构添加一个基于 SMCCC（SMC Calling Convention）的缓存无效化（cache invalidate）后端的 RFC 补丁。作者 Srirangan Madhavan 来自 NVIDIA，其目标是在非一致性 DMA 场景下，通过固件调用来完成缓存的 clean 与 invalidate 操作，并将该实现注册到通用的缓存一致性框架（cache coherency framework）中。补丁在 `arch/arm64/mm/cache_maint.c` 中新增了一个驱动，利用 `arm-smccc` 接口查询并调用平台的缓存维护能力，同时处理固件返回的 `BUSY` 和 `RATE_LIMITED` 临时性错误，以有限重试的方式保证操作的可靠性。

技术动机方面，部分 ARM64 系统（尤其是涉及安全分区或异构计算的 SoC）不具备硬件维护的一致性，或者需要将缓存操作委托给监控层固件。通过 SMCCC 这种标准化接口，内核可以在不了解硬件细节的情况下安全地执行缓存维护。补丁尝试将这种机制抽象为通用框架的一部分（`include/linux/cache_coherency.h`），使得非架构特定的 DMA 映射代码无需直接与 SMCCC 交互。

讨论中的关键争议点在于代码的位置。作者最初将文件放在 `arch/arm64/mm/` 下，并使用 `CONFIG_ARCH_HAS_CPU_CACHE_INVALIDATE_MEMREGION` 进行编译控制。但维护者 Jonathan Cameron 和 Conor Dooley 都倾向于将其移至 `drivers/cache/`，因为他们认为这本质上是属于某个子系统的驱动（即便该子系统与架构紧密耦合）。Conor 以 RISC-V 平台类比，指出如果是通过 `ecall` 进入 SBI 固件，他会要求放入 `drivers/cache`；同样，这里操作的执行依赖于设备特定的固件，与 `clk-scmi` 之类驱动的处境类似，因此放入通用缓存驱动目录更为合适。此外，Jonathan 还提出未来可能需要对缓存操作进行更智能的融合（fusing），以提升性能。

## 参与讨论人员
- Srirangan Madhavan (NVIDIA) —— 补丁作者
- Jonathan Cameron —— 缓存一致性框架维护者
- Conor Dooley (kernel.org) —— 参与讨论并提出代码位置建议
- Will Deacon 和 Catalin Marinas —— ARM64 维护者（被提及但未直接参与本次讨论）

## 达成的结论
讨论尚未形成最终共识，但目前维护者之间的意见高度一致：代码应当从 `arch/arm64/mm/` 移动至 `drivers/cache/`，并使用该子系统提供的 Kconfig 选项进行编译，而非依赖 `ARCH_HAS_CPU_CACHE_INVALIDATE_MEMREGION`。其他技术细节（如对 `BUSY`/`RATE_LIMITED` 的处理策略）未出现异议，但 Jonathan 提出的“操作融合”属于远期改进，暂无立即行动要求。

## 下一步改进方向
1. 将 `cache_maint.c` 的实现从 `arch/arm64/mm/` 移动到 `drivers/cache/` 并相应调整 MAINTANERS 条目。
2. 删除 `arch/arm64/mm/Makefile` 中的相关编译条目，改用 `drivers/cache/` 下的 Kconfig 控制。
3. 考虑在后续版本中增加缓存操作的批量融合逻辑（例如将连续的 clean+invalidate 调用合并为范围操作），但此项非阻塞性需求，可以后续通过独立补丁追踪。
4. 等待 ARM64 维护者对文件位置选择的最终确认。

## 新增补丁
本次邮件仅包含 `[RFC PATCH 2/2]` 的初次发布，未出现更新版本。补丁增加了 `MAINTAINERS`、`arch/arm64/mm/Makefile` 以及新文件 `arch/arm64/mm/cache_maint.c`（共 182 行插入），尚未因讨论意见进行修改。

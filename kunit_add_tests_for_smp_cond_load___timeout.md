# kunit: add tests for smp_cond_load_*_timeout()

---

## 更新 - 2026-05-21 01:30 UTC

## 核心话题
本邮件是 Ankur Arora 提交的 [PATCH v11 1/2] 补丁，目的是为 Linux 内核中的 `smp_cond_load_*_timeout()` API 添加 KUnit 单元测试。该系列补丁针对 ARM64 架构，但此补丁直接修改 `lib/` 目录下的测试基础设施。补丁说明指出，新添的测试覆盖成功和失败两种情况：成功场景中，会启动一个内核线程去设置条件变量，然后检查 `smp_cond_load_*_timeout()` 能否在条件满足后返回；失败场景中，条件永远不被设置，函数必须等到超时才返回，且不能提前返回。

关键技术改动来源于 Mark Brown 此前报告的一个测试错误（https://lore.kernel.org/lkml/agr_RxvNtfASfevg@sirena.org.uk/）。邮件中的“Note”部分列出了三项主要修正：
1. **放宽成功场景的时序约束**：旧版本测试假设成功时 `smp_cond_load_relaxed_timeout()` 必须在超时前返回（即运行时间 ≤ timeout_ns）。但这并不严格成立，因为调度延迟或硬件行为可能导致即便条件已满足，调用仍可能在超时时刻附近才返回。修正后，只要求失败场景下函数不能早于超时返回（运行时间 ≥ timeout_ns），成功场景不再检查精确时序。
2. **移除内核线程辅助**：原测试在成功场景中会启动一个内核线程去设置等待的位。为了避免在仿真或资源受限环境下因时序不确定导致的虚假失败，补丁移除了该内核线程，改为在测试代码中直接设置条件位。
3. **参数化测试用例**：将测试逻辑参数化，以便更容易扩展和维护，减少样板代码。

补丁文件为 `lib/tests/barrier-timeout-test.c`，共新增 128 行测试代码，并相应地修改了 `lib/Kconfig.debug` 和 `lib/tests/Makefile`，使测试可以在启用 KUnit 的情况下编译运行。这次提交是整个 v11 系列的第一部分，后续补丁可能涉及 ARM64 架构下对这些超时 API 的具体实现或优化。

## 参与讨论人员
- Ankur Arora (Oracle) — 补丁作者
- Mark Brown (Arm) — 报告了前一版本的测试错误，虽然本邮件中没有直接回复，但他的报告是本次修正的直接原因
- Andrew Morton (Linux Foundation)
- Arnd Bergmann (

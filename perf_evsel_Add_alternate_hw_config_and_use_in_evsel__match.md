# perf evsel: Add alternate_hw_config and use in evsel__match

---

## 更新 - 2026-05-20 18:19 UTC

## 核心话题
该邮件源自 Linux 6.12 稳定版审查补丁，内容是将上游 commit 22a4db3c3603（“perf evsel: Add alternate_hw_config and use in evsel__match”）回植到 6.12 稳定分支。补丁主要解决 perf 工具在匹配硬件事件（如 instructions、cycles）时的准确性问题，尤其在 stat-shadow 的硬编码 metrics 计算中。以往仅依赖 evsel 的 name 字段进行匹配存在致命缺陷：name 会在解析或初始化过程中被修改，直接使用 strstr 简单匹配又过于粗糙，重新解析事件名称则显得笨拙。为此，补丁引入 `alternate_hw_config` 字段，在事件解析阶段就保存下“传统硬件事件名称”（legacy hardware event name），之后在 `evsel__match` 中直接利用该字段进行比对，从而避免名称失真和误匹配。

本补丁的直接触发场景虽然针对 perf 通用代码，但其背景与 ARM64 架构密切相关。邮件明确抄送了 `linux-arm-kernel@lists.infradead.org`，提交者 James Clark 来自 Linaro，而 Linaro 长期维护 ARM 生态的 perf 工具支持。ARM64 平台的 PMU 事件命名与 x86 存在差异（例如某些实现用 `cpu_cycles` 而非 `cycles`），且内核中硬编码的 metrics 公式期望匹配标准硬件事件标识。若匹配错误，会导致 `perf stat` 的派生指标（如 IPC、分支预测率）计算失败或数值偏离。该补丁通过保留解析时确定的“规范”硬件事件名，使得在 ARM64 等架构上也能可靠地将用户事件映射到 metrics 所需的正确 event ID，保证了跨架构 perf 工具行为的一致性。上游补丁签名链中包含 Namhyung Kim、Kan Liang 等 perf 维护者的 Ack，进一步说明该改动是解决包括 ARM64 在内的多种架构共性问题的正确方案。

## 参与讨论人员
- Greg Kroah-Hartman：Linux 稳定版维护者，负责发送该 stable review 补丁。
- Ian Rogers (Google)：补丁作者。
- James Clark (Linaro)：补丁提交者（Patch submitter），代表 ARM 生态。
- Namhyung Kim：perf 子系统维护者，提供 Acked-by。
- Kan Liang (Intel)：提供 Acked-by。
- 其他 Cc 人员：Yang Jihong、Dominique Martinet、Colin Ian King、Howard Chu、Yunseong Kim、Ze Gao、Yicong Yang、Weilin Wang、Will Deacon、Mike Leach、Jing Zhang、Yang Li、Leo Yan、Andi Kleen、Athira Rajeev、John Garry 等，以及 ARM 内核邮件列表。

## 达成的结论
此为稳定版补丁审查邮件，Greg Kroah-Hartman 在邮件中声明“If anyone has any objections, please let me know.”，而后续未出现任何反对意见。补丁已作为上游 commit 22a4db3c3603 的回植被纳入 6.12 稳定队列，且明确标注为另一个补丁（c9ef786c0970 “perf cgroup: Update metric leader in evlist__expand_cgroup”）的回溯依赖（Stable-dep-of）。因此可以认为补丁被顺利接受，共识达成，将在 6.12.y 稳定版本中发布。

## 下一步改进方向
- 需要验证该补丁在 ARM64 实际平台（特别是具有不同 PMU 实现的 SoC）上 `perf stat --metric` 等场景下的正确性，确保不再出现事件匹配失败导致的零值或错误指标。
- 依赖的补丁 c9ef786c0970（cgroup metric leader 修复）也需一并合入并进行回归测试，避免 cgroup 模式下 metrics 计算中断。
- 关注稳定版发布后的用户反馈，若 ARM64 或其他架构仍有类似匹配问题，需进一步优化 `evsel__match` 逻辑或扩展 `alternate_hw_config` 的覆盖范围。

## 新增补丁
本邮件中未出现新的补丁版本，仅是对单一上游补丁的直接回植，无 v2、v3 等迭代。该补丁以 `[PATCH 6.12 374/666]` 的形式合入，属于稳定版补

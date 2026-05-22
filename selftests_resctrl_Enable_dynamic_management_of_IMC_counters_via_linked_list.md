# selftests/resctrl: Enable dynamic management of IMC counters via linked list

---

## 更新 - 2026-05-22 17:05 UTC

## 核心话题
本邮件是 Yifan Wu 提交的补丁系列 v3 的第三部分（3/3），主题是对内核源码树中 `tools/testing/selftests/resctrl/resctrl_val.c` 的重构，旨在**启用基于链表的 IMC（集成内存控制器）计数器动态管理**。当前代码使用一个静态数组 `imc_counters_config[MAX_IMCS]` 来存放检测到的 IMC 计数器配置，并通过宏 `MAX_IMCS` 将数量硬性上限设为 40。在 `parse_imc_read_bw_events` 函数中，每检测到一个 IMC 计数器事件，会检查当前计数 `*count` 是否超过 `MAX_IMCS`，若超过则报错并终止。这种设计在拥有超过 40 个 IMC 的 ARM64 平台上会直接导致剩余计数器被忽略，使得内存带宽监控测试不完整甚至初始化失败，限制了测试框架的可移植性和可扩展性。

补丁移除了 `MAX_IMCS` 宏、静态数组 `imc_counters_config` 以及全局计数器 `imcs`，转而引入一个内核链表头 `LIST_HEAD(imc_counters_list)`。函数 `parse_imc_read_bw_events` 的参数也从接受 `unsigned int *count` 改为仅接受 `imc_dir` 和 `type`，内部使用 `bool found_event` 标记是否找到了事件，并在检测到有效计数器时，通过 `calloc` 动态分配 `struct imc_counter_config` 节点，然后将其插入全局链表。这一改动删除了“计数器超限”的错误分支，使系统能自动适应硬件实际提供的 IMC 数量，无需人为预设上限。技术动机明确：ARM64 服务器的 IMC 数量常有较大差异，硬编码上限会破坏测试的正确性；动态链表管理不仅解决了上限问题，还为将来可能的运行时增删操作提供了更灵活的数据结构基础。邮件中强调 “Enable dynamic management of IMC counters”，表明这不仅是消除限制，更是设计范式的升级。

## 参与讨论人员
- **Yifan Wu** (华为) — 补丁提交者，邮箱 `wuyifan50@huawei.com`。

邮件线程仅含此一封补丁提交，无其他回复者。

## 达成的结论
该邮件为独立的补丁提交，未附有任何社区成员或维护者的回复，因此**尚未达成任何结论**。补丁目前处于待审核状态，等待后续讨论。

## 下一步改进方向
1. **社区审查**：需由 resctrl/test 模块的维护者或其他开发者审阅链表操作的正确性，特别是节点分配后的插入与遍历逻辑，确保不会

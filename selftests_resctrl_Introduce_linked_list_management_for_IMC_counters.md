# selftests/resctrl: Introduce linked list management for IMC counters

---

## 更新 - 2026-05-22 17:05 UTC

## 核心话题
该讨论线程仅包含一封提交补丁的邮件，由华为的 Yifan Wu 发送。补丁标题为“[PATCH v3 1/3] selftests/resctrl: Introduce linked list management for IMC counters”，属于一个包含 3 个补丁的系列（v3 版本）中的第一个。核心目的是将 **resctrl 内核自测试** 中对 **IMC（Integrated Memory Controller）计数器** 的管理方式从固定大小的静态数组重构为**动态链表**。

补丁明确指出，原有的静态数组方案存在固定大小限制，兼容性和可扩展性不足（“fixed size constraints and limited compatibility and scalability”）。为解决这些问题，补丁引入了基于 Linux 内核链表 (`linux/list.h`) 的动态管理基础设施。

该补丁的具体改动包括：
- 在 `resctrl.h` 中增加 `#include <linux/list.h>`，为链表操作提供基础数据结构。
- 在 `resctrl_val.c` 中新增 **内存分配与清理函数**（函数名可能为 `setup_read_mem_bw_imc()` 和 `cleanup_read_mem_bw_imc()`，虽然邮件被截断，但从后续调用可推断），用于动态分配和释放 IMC 计数器配置。
- 在 `mba_test.c` 和 `mbm_test.c` 各自的清理函数（`mba_test_cleanup()` 和 `mbm_test_cleanup()`）末尾添加对 `cleanup_read_mem_bw_imc()` 的调用，确保测试结束后释放链表占用的内存，避免资源泄漏。
- 修改范围涉及 4 个文件，新增 29 行，删除 2 行，体现了从静态数组到动态链表的转换是逐步的，本补丁仅搭建基础和增加清理调用，后续补丁可能完成实际链表逻辑的替换。

由于邮件被截断，无法看到链表节点结构体的定义以及 `setup_read_mem_bw_imc()` 的完整实现，但可推断该结构体将包含如 CPU 编号、IMC 实例 ID、perf_event 描述符等字段，并通过 `list_head` 串联。动态链表能按需分配节点，免除原始数组大小预定义的硬编码，使测试能适应不同硬件配置（如不同数量的 IMC 控制器），极大提升了可移植性和维护性。

## 参与讨论人员
- Yifan Wu (华为) — 补丁作者与唯一发件人，负责提交 v3 系列补丁。

## 达成的结论
该线程目前**仅有一封补丁提交邮件**，尚无任何回复或评审意见，因此**未达成任何技术结论或共识**。补丁状态为“待审核”（pending review）。

## 下一步改进方向
由于补丁系列尚未得到社区反馈，下一步的自然流程包括：
1. **内核自测试维护者或相关领域专家对补丁进行评审**，检查链表操作的线程安全性、内存泄漏风险、与现有 perf 事件的交互等。
2. **确认补丁系列其余部分（2/3、3/3）是否正确应用了动态链表**，并验证整个测试套件功能不受影响。
3. 提交者需确保**改动通过所有 resctrl 自测试**，特别是在不同 Intel 平台（如支持 ITBM 的至强处理器）上的兼容性。
4. 根据评审意见修改代码，如有必要发布 v4 版本。

## 新增补丁
- **[PATCH v3 1/3] selftests/resctrl: Introduce linked list management for IMC counters** — 本补丁为系列首版，引入了链表管理的基础设施和清理函数，为后续动态化 IMC 计数器管理奠定基础。补丁系列完整情况未知，但已知至少包含共 3 个补丁。

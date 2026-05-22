# arm64/vdso: Enable SFrame generation in vDSO

---

## 更新 - 2026-05-22 10:51 UTC

## 核心话题
该邮件讨论围绕为 ARM64 架构的虚拟动态共享对象（vDSO）启用 SFrame（一种栈回溯格式）生成展开。Jens Remus 提交了补丁 `[PATCH v1 3/4] arm64/vdso: Enable SFrame generation in vDSO`，旨在将此前为 x86 实现的方案（见 Josh 的补丁）复制到 ARM64 平台。其技术动机是：在 vDSO 库中生成 `.sframe` 节区，使内核和用户空间的栈回溯工具（如 perf）能够穿透 vDSO 进行准确回溯。该补丁的具体做法包括：在 vDSO 中保留所有函数符号（包括 `.symtab` 中不输出但有助于栈追踪的符号），并利用 binutils 2.46 引入的 SFrame V3 格式支持，仅当汇编器支持时生成 `.sframe`、将其标记为 KEEP 并创建 `GNU_SFRAME` 程序头，否则显式丢弃相关节区。

然而，该补丁与 Dylan Hatch 提出的另一项补丁（`[PATCH v3 2/8] arm64, unwind: build kernel with sframe V3 info`）存在潜在冲突。Dylan 的补丁涉及在内核构建中启用/禁用 SFrame，并通过 `CC_FLAGS_REMOVE_VDSO` 移除某些标志；而 Jens 的补丁需要在 vDSO 的 `CC_FLAGS_ADD_VDSO`（及 `AS_FLAGS_ADD_VDSO`）中添加 `-Wa,--gsframe-3`。这会导致两个补丁对同一编译标志集的添加与移除产生碰撞。因此，核心讨论点是如何协调这两项工作，使 vDSO 的 SFrame 生成与内核自身的 SFrame 构建条件保持合理隔离。Dylan 在回复中提出了期望的两个不变条件：（1）若 `HAVE_UNWIND_KERNEL_SFRAME=n`，内核不得以 `.sframe` 构建；（2）若 `AS_SFRAME3=y`，vDSO 必须带有 `.sframe`。他指出 `HAVE_UNWIND_KERNEL_SFRAME=y` 隐含 `AS_SFRAME3=y`，因此可以考虑从 `CC_FLAGS_REMOVE_VDSO` 中删除 `CC_FLAGS_SFRAME`，并调整相关定义。邮件中 Dylan 还给出了一段具体的 Makefile diff 草案（原文被截断），试图以此解决冲突。

## 参与讨论人员
- Jens Remus (linux.ibm.com)  
- Dylan Hatch (google.com)

## 达成的结论
尚未达成明确结论。Dylan 提出了技术方案（调整 Makefile 条件编译和标志移入移出）来化解冲突，Jens 在回信中感谢了反馈但未见表达最终同意或拒绝。讨论仍处于方案协商阶段，需要进一步确认或修改。

## 下一步改进方向
1. 需要整合 Jens 的 vDSO SFrame 补丁与 Dylan 的内核 SFrame V3 构建补丁，确保在 `HAVE_UNWIND_KERNEL_SFRAME=n` 时内核不生成 `.sframe`，但 vDSO 只要汇编器支持 SFrame3 即应生成。  
2. 具体代码修改方向参考 Dylan 提议：可能从 `CC_FLAGS_REMOVE_VDSO` 中移除 `CC_FLAGS_SFRAME`，或将相关定义移动到更合适的 Makefile 位置，并在 vDSO 专用标志中正确添加 `-Wa,--gsframe-3`，同时考虑与现存标志移除逻辑的兼容性。  
3. 需要进一步讨论和测试该方案，确保不影响其他架构或不引入意外的标志覆盖。

## 新增补丁
本邮件讨论中未出现新的补丁版本，原始补丁仍为 v1。

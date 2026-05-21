# KVM: arm64: Fix rollback in hyp_trace_buffer_share_hyp()

---

## 更新 - 2026-05-21 13:46 UTC

## 核心话题
本次讨论围绕 Linux 内核 ARM64 架构下的 KVM（内核虚拟机）跟踪机制中的一个回滚（rollback）缺陷展开。补丁由 Vincent Donnefort 提交，旨在修正 `hyp_trace_buffer_share_hyp()` 函数在将跟踪缓冲区共享给 pKVM/nVHE 模式下的 hyp（hypervisor）时，因共享失败而执行清理时出现的两个严重遗漏。

第一个问题是：当进入按 CPU 逐个共享页面（`rb_desc->page_va[p]`）的循环后，如果某次 `__share_page()` 调用返回错误，原有的回滚路径仅对已经成功共享的若干 `page_va` 页面调用 `__unshare_page()` 进行取消共享，却完全忽略了在此循环之前已成功共享的元数据页（`meta_va`）。该元数据页在循环开始前即通过 `__share_page(rb_desc->meta_va)` 完成共享，但回滚时并未将其释放，导致资源泄漏或不一致的状态。如邮件中所述：“如果共享一个页面失败，回滚路径在 hyp_trace_buffer_share_hyp() 中遗漏了取消共享元数据页 (meta_va)，该页在进入页面共享循环之前已成功共享。”

第二个问题是：当共享失败并跳出循环后，代码会调用 `hyp_trace_buffer_unshare_hyp()` 进行全局清理，但传递的 CPU 索引参数有误。原始代码为 `hyp_trace_buffer_unshare_hyp(trace_buffer, cpu--)`，其中 `cpu` 是循环变量，此时若在循环中因 `ret` 非零而 `break`，`cpu` 的值正好是第一个失败的 CPU 索引。然而，循环内部的局部回滚已经对该失败 CPU（及之前成功共享的所有 CPU）的页面逐一执行了 `__unshare_page()`。若再以 `cpu--`（即当前 `cpu` 值，再事后递减）调用全局清理，会导致对该 CPU 的页面进行重复的取消共享操作，可能引发引用计数错误或其他并发问题。补丁修正为 `--cpu`，使得传递给 `hyp_trace_buffer_unshare_hyp()` 的是上一个已成功处理（且已经局部回滚）的 CPU 索引，从而避免重复操作。

同时，循环内部的回滚计数器逻辑也做了修改，从 `for (p--; p >= 0; p--)` 改为 `while (--p >= 0)`，使索引先递减再判断，更简洁且与修正后的 CPU 索引处理风格一致。补丁中添加的 `__unshare_page(rb_desc->meta_va)` 则确保元数据页也能在出错时被正确释放。

该缺陷由内核测试机器人 Sashiko 报告，并被标记为 `Fixes: 3aed038aac8d ("KVM: arm64: Add trace remote for the nVHE/pKVM hyp")`，意在修复引入 hyp 远程跟踪功能时伴生的回滚逻辑漏洞。

## 参与讨论人员
- Vincent Donnefort (Google) —— 补丁作者
- Sashiko (kernel.org 测试机器人) —— 缺陷报告者（非直接讨论参与者）

## 达成的结论
此邮件仅为独立的补丁提交（v2 系列中的第 2/3 封），在给出的线程片段中没有后续回复或讨论。因此，未形成任何关于补丁的评审结论或共识。该修复方案有待 ARM64 KVM 维护者审核与接纳。

## 下一步改进方向
1. 该补丁需要得到 ARM64 或 KVM 子系统的维护者审查，确认回滚顺序和索引处理的正确性。
2. 需要评估是否存在其他类似遗漏的资源清理路径，并在整个 hyp_trace 模块中进行一致性检查。
3. 应对修复后的代码进行充分的测试，尤其是模拟共享页面失败的各种错误注入场景，验证不再出现资源泄漏或重复取消共享。
4. 补丁提交人或许需要根据审查反馈对提交说明或代码风格做进一步微调，以及确保整个 v2 补丁系列（1/3 和 3/3）逻辑连贯。

## 新增补丁
- **[PATCH v2 2/3] KVM: arm64: Fix rollback in hyp_trace_buffer_share_hyp()**  
  修复两个回滚问题：① 在共享页面失败时，增加对已共享的元数据页 (`meta_va`) 的 `__unshare_page()` 调用；② 修正传递给 `hyp_trace_buffer_unshare_hyp()` 的 CPU 索引，从 `cpu--` 改为 `--cpu`，避免重复取消共享；同时将循环内回滚索引改为 `--p` 形式。

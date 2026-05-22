# KVM: arm64: selftests: Add shadow_stage2 test

---

## 更新 - 2026-05-22 11:02 UTC

## 核心话题
本邮件讨论的核心是 Wei-Lin Chang 发布的补丁系列（v3，第5/9个）中的“KVM: arm64: selftests: Add shadow_stage2 test”。该补丁意在为 KVM/arm64 引入一个新的自测用例 `shadow_stage2`，用于验证 KVM 的“影子阶段二（shadow stage-2）页表管理”代码的正确性。在 ARM 嵌套虚拟化场景下，当 L1 虚拟机运行 L2 虚拟机且 L1 为 L2 启用自己的阶段二地址转换时，KVM 需要将 L2 的 IPA → PA 的映射“影子化”到真实的阶段二页表中，这就是 shadow stage-2 要解决的问题。本次提交的测试版本相对简单，类似于已有的 `hello_nested` 测试：它启动一个嵌套虚拟机（L2），但目前没有为 L2 开启阶段二地址转换，因此只能极小程度地触发 KVM 中的 shadow stage-2 逻辑。原作者在补丁说明中明确表示“right now it doesn't turn on stage-2 for the nested guest (L2) yet, therefore the shadow page table code in KVM will only be triggered minimally now.” 这表明该测试是一个渐进式的基础框架，未来会逐步扩展以覆盖更复杂的影子页表场景。

从代码片段可以看到，测试文件 `tools/testing/selftests/kvm/arm64/shadow_stage2.c` 利用了 `nested.h`、`processor.h` 等已有测试基础设施，定义了一些常量（如 `XLATE2GPA`、`L2STACKSZ`）和 L2 的退出状态码（`L2SUCCESS`、`L2FAILED`、`L2SYNC`），基本结构确实与现有 `hello_nested` 类似。整个补丁系列的目标是完善对 KVM 影子阶段二页表的支持，而本次测试的加入是为了保障该特性的健壮性，以自测形式嵌入到内核测试框架中。邮件线程虽然被截断，但可以推断 Itaru Kitayama 很可能是对该补丁进行测试、评论或提出疑问，其回复内容未能完整显示，因此具体讨论细节无法还原。

## 参与讨论人员
- **Itaru Kitayama** (富士通, itaru.kitayama@fujitsu.com)
- **Wei-Lin Chang** (Arm, weilin.chang@arm.com)

## 达成的结论
由于邮件列表归档被截断，Itaru Kitayama 的具体回复内容缺失，无法判断其评论是认可、测试结果报告还是修改建议，因此本线程是否就补丁达成共识无法确定。从已有信息看，这更像是单轮反馈，尚无明确的“结论”。

## 下一步改进方向
若 Itaru Kitayama 的原始回复中包含了测试失败、编译问题或设计质疑，则下一步需要针对性修改测试代码或补丁逻辑；若回复仅为测试确认或评论，则后续改进方向应围绕补丁本身的未完工作展开，即：**为 L2 开启阶段二地址转换，从而充分触发 shadow stage-2 页表管理代码，扩展测试覆盖范围**，确保影子页表在各种映射场景下（如不同页面大小、权限、设备内存等）的行为正确。此外，还需注意该补丁作为 v3 系列的一部分，整个系列的其他反馈也会影响本测试的最终形态。

## 新增补丁
本邮件为对补丁的评论/测试反馈，不包含新版本的补丁。截至该邮件，最新版补丁仍是 Wei-Lin Chang 提交的 **v3 5/9**。

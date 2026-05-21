# arm_ffa, KVM: Fix FF-A emad offset calculations

---

## 更新 - 2026-05-20 20:49 UTC

## 核心话题
本邮件讨论围绕ARM FF-A（Firmware Framework for Arm A-profile）架构中“端点内存访问描述符”（Endpoint Memory Access Descriptor, EMAD）偏移计算的错误展开。在FF-A 1.0版本中，内存区域描述符的头部（`ffa_mem_region`）之后没有显式指定EMAD数组的起始偏移，因此Linux内核中的`arm_ffa`驱动和pKVM（受保护的KVM）组件均默认EMAD紧跟在头部之后，即偏移为`sizeof(struct ffa_mem_region)`。但FF-A 1.1规范引入了`ep_mem_offset`字段，用于显式指定EMAD数组相对于内存区域结构体起始位置的偏移，驱动和hypervisor必须使用该字段来定位描述符，而不是硬编码假设。

如果没有正确遵循这一规范变化，将导致两处严重问题：
1. **驱动侧越界写**：`arm_ffa`核心驱动在构造分片内存传输描述符时，若EMAD并不紧接头部，仍按头部大小固定偏移写入，可能覆盖后续数据或写入到未预期的区域，触发`ffa_setup_and_transmit()`中的越界写。
2. **pKVM侧校验缺失与误判**：受保护的KVM在安全侧对来自正常世界的FF-A内存共享请求进行校验时，先前实现强制要求EMAD必须紧挨头部，若偏移字段给出的位置不同，会错误拒绝合法的请求；同时缺少对描述符偏移是否超出共享内存缓冲区（mailbox）边界的校验，可能导致读取受保护内存区域之外的敏感数据。

该补丁系列（v4）对此进行了系统性修复：
- 修正`arm_ffa`驱动中的描述符偏移计算逻辑，改为使用`ep_mem_offset`字段，并加入基于`max_fragsize`的边界检查。
- 放宽pKVM中对描述符位置的严格强制要求，不再假设描述符必须紧随头部，而是依据偏移字段定位，并增加偏移是否位于mailbox内（即`do_ffa_mem_reclaim()`中的边界校验）的检查。
- 系列中还包含对`optee: ffa: Add NULL check in optee_ffa_lend_protmem`等附带问题的修复，这些问题由Sashiko在测试中发现。

系列作者强调，这些改动使内核行为与FF-A 1.1规范对齐，消除了因旧版本假设带来的安全漏洞与兼容性问题。

## 参与讨论人员
- **Mostafa Saleh** (Google) —— 补丁提交者，负责其中3个修复（optee空指针检查、arm_ffa驱动越界写、KVM边界检查）。
- **Sebastian Ene** (Google) —— 系列共同作者，提供另外2个补丁（主要涉及arm_ffa驱动和pKVM的EMAD偏移计算修复）。
（由于提供的是邮件线程头部，未见后续回复，可能另有审核者如Marc Zyngier、Will Deacon等ARM KVM维护者在后续参与，但本片段未列出。）

## 达成的结论
邮件仅为补丁提交通知，尚未形成最终结论。该系列补丁处于v4版本，正在等待维护者审查。从版本历史来看，v3->v4已根据上一轮审查意见进行了修正（“Address review comments and fix Sashiko bugs”），但未明确说明已获得Acked-by或Reviewed-by标签，因此尚未达到可合入状态。结论暂为：**补丁待审核，无最终合入决定**。

## 下一步改进方向
1. **深入审核**：需要ARM FF-A维护者（如Sudeep Holla）及KVM/arm64维护者对补丁进行详细代码审查，确认偏移计算逻辑和边界检查的正确性。
2. **测试验证**：在真实的FF-A 1.1环境及pKVM安全分区场景下验证，确保驱动和hypervisor均能正确处理合法偏移，并拒绝off-bound情况。
3. **可能补充文档**：若规范细节容易误解，或许需要在内核文档中增加注释，说明`ep_mem_offset`的使用原则。
4. **修复Sashiko所报其它bug**：邮件提及Sashiko在测试中发现了额外问题，且已在此系列中一并解决，需确认这些问题是否彻底修复。

## 新增补丁
- **补丁版本**：v4
- **补丁数量**：5个
- **主要变更**：
  - v3->v4：响应上一轮评审意见，并修复Sashiko在测试中发现的额外问题。
  - v2->v3：修正了`arch/arm64/kvm/hyp/nvhe/ffa.c`中缺失`sizeof`导致的拼写错误。
  - v1->v2：在pKVM侧，删除了对EMAD必须紧接内存区域头部的严格位置检查，改为接受偏移字段指示的任意有效位置，以符合FF-A规范并避免对驱动内存布局做假设。
- **补丁组成**：
  - Mostafa Saleh (3个): optee: ffa的NULL检查；firmware: arm_ffa修复越界写；KVM: arm64修复回收时的边界检查。
  - Sebastian Ene (2个): 针对arm_ffa驱动与pKVM的EMAD偏移计算修复（具体标题因邮件截断不全，但应包含`firmware: arm_ffa: Fix EMAD offset ...`和`KVM: arm64: ...`）。

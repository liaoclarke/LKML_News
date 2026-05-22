# [DO NOT MERGE] s390: Expose protected virtualization through cc_platform_has()

---

## 更新 - 2026-05-22 09:57 UTC

## 核心话题
该补丁旨在将IBM s390架构的受保护虚拟化（Protected Virtualization）支持集成到内核的通用机密计算平台（confidential computing platform）抽象层中。目前，s390保护虚拟化guest会强制所有DMA映射为不加密（通过`force_dma_unencrypted()`返回true），但并未通过`cc_platform_has()`框架明确告知内核其具备内存加密能力。本补丁通过选择`ARCH_HAS_CC_PLATFORM`并实现`cc_platform_has()`函数，以`CC_ATTR_MEM_ENCRYPT`属性为保护虚拟化guest返回true，从而将s390的机密计算特性标准化地暴露给内核其余部分。

发件人Aneesh Kumar K.V明确将补丁标记为`[DO NOT MERGE]`，说明目前仅为演示或前置测试用途。补丁中的代码变更简洁：在`arch/s390/Kconfig`中添加`select ARCH_HAS_CC_PLATFORM`；在`arch/s390/mm/init.c`中新增`cc_platform_has()`实现，当`attr`为`CC_ATTR_MEM_ENCRYPT`时调用`is_prot_virt_guest()`判断是否处于保护虚拟化环境。该实现与已有的`force_dma_unencrypted()`逻辑保持一致，都依赖同一个底层条件。抄送列表中包括了IBM的Halil Pasic、Matthew Rosato和Jaehoon Kim，表明他们可能是s390保护虚拟化相关代码的维护者或利益相关者，需要关注此改动。

## 参与讨论人员
- Aneesh Kumar K.V (Arm) — 补丁提交者，邮箱 aneesh.kumar@kernel.org
- Halil Pasic (IBM) — 被抄送
- Matthew Rosato (IBM) — 被抄送
- Jaehoon Kim (IBM) — 被抄送

## 达成的结论
本邮件为单向的补丁提交，未产生回复与讨论，因此未达成任何共识或结论。补丁本身的状态是不应被合入（DO NOT MERGE），表明作者当前无意正式将其并入主线，可能仅用于辅助更大系列中其他补丁的构建或验证。

## 下一步改进方向
由于该补丁被标记为`[DO NOT MERGE]`，下一步可能是等待整个补丁系列（v5 共20个补丁）中其他依赖项的完善，或者获取s390维护者的正式确认以确保内存加密属性的抽象方式适用于他们的保护虚拟化机制。如果决定正式提交流程，需要移除`[DO NOT MERGE]`标记，并可能需要补充说明为何s390应采用`cc_platform_has()`替代或补充现有的`force_dma_unencrypted()`，以及该修改是否会影响其他依赖于机密计算属性的通用代码路径。另外，补丁中`EXPORT_SYMBOL_GPL`的使用也需要审查是否确实需要导出符号给模块。

## 新增补丁
本邮件为补丁系列`v5`中的第02/20号补丁，未在此线程中发布新的补丁版本。

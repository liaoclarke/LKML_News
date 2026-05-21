# firmware: arm_ffa: Fix Endpoint Memory Access Descriptor offset calculation

---

## 更新 - 2026-05-21 13:55 UTC

## 核心话题
本讨论围绕 Linux 内核中 ARM FF-A（Firmware Framework for Arm A-profile）子系统的一个补丁展开，该补丁修正了端点内存访问描述符偏移量的计算方式，使其严格遵循 FF-A 规范。  
在之前的实现中，计算端点内存访问数组的起始位置时，直接硬编码使用了 `sizeof(struct ffa_mem_region)`，这不符合规范中由描述符自身字段 `ep_mem_offset` 来指定偏移的要求。该补丁（v4 版本）的核心改动是将偏移量来源切换为描述符中的 `ep_mem_offset`，并为了逻辑正确，将 `ffa_mem_region_additional_setup()` 函数提前调用，以在早期完成相关字段的初始化。同时，新增了对计算出的描述符偏移量进行合理性检查的逻辑，确保其不会超过 `max_fragsize`，防止因非法偏移导致越界访问。  
Sudeep Holla 在审查中指出，该补丁的核心变更与 v3 版本保持一致，仅改进了错误检查部分，因此其之前的审查意见依然有效，并给出了 Reviewed-by 标签。这表明该修复在技术上是合理的，既纠正了规范遵从性问题，又通过增强的错误检查提升了代码的健壮性。

## 参与讨论人员
- Sudeep Holla (kernel.org) — 审查者，提供了 Reviewed-by 标签
- Mostafa Saleh — 补丁提交者
- Sebastian Ene (Google) — 补丁的原始作者

## 达成的结论
已达成共识。Sudeep Holla 明确表示 “review still applies” 并给出 `Reviewed-by: Sudeep Holla <sudeep.holla@kernel.org>`，说明该 v4 补丁已通过审查，可以被接纳合并。

## 下一步改进方向
该补丁已获得正式审查通过，下一步应当由维护者或提交者将其收入相应的子系统树（如 ARM FF-A 维护者树），准备向主线内核合并。不需要进一步代码改动或讨论，除非后期测试发现新的边缘情况。

## 新增补丁
本邮件讨论的是 v4 版本的补丁（`[PATCH v4 3/5]`）。相对于 v3 版本，主要变化是改进了错误检查（improved error checking），而其余核心修改保持不变。邮件中没有出现更新的 v5 版本。

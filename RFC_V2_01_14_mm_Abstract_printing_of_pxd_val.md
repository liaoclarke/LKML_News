# [RFC V2 01/14] mm: Abstract printing of pxd_val()

---

## 更新 - 2026-05-21 10:42 UTC

## 核心话题
该邮件讨论围绕一个补丁展开，该补丁旨在抽象化内核中打印 `pxd_val()` 这类页表项值的格式。原补丁作者 Anshuman Khandual 在当前代码中直接使用 `%08llx` 打印 `pgdv`、`p4dv` 等变量，但为了适配不同架构下 `pxd_val()` 可能的宽度差异，引入了 `__PRIpxx` 和 `__PRIpxx_args()` 宏，将打印变为类似 `pr_alert("pgd:%" __PRIpxx " p4d:%" __PRIpxx "\n", __PRIpxx_args(pgdv), __PRIpxx_args(p4dv));` 的形式。这种写法虽然类型安全，但可读性严重下降。

Intel 工程师 Dave Hansen 建议使用新的 printk 格式说明符，例如 `%pT`，将打印简化为 `pr_alert("pgd:%pT p4d:%pT\n", &pgd, &p4d);`，并可省去中间变量。他认为这样更简洁，且可能更适合内核中少数需要打印这类值的场景。

David Laight 则提出了不同意见，认为增加一个仅用于少数地方的 `%p` 变体反而会降低代码的可读性，因为它违背了人们对标准格式说明符的直觉。他建议采用折中方案：定义一个本地辅助函数，比如 `fmt_pdgv(buf, pgdv)`，将值格式化为字符串，然后在 `pr_alert` 中使用 `%s` 输出，如 `pr_alert("...%s...", ...fmt_pdgv(pdgv_buf, pgdv)...)`。这样既保持了打印语句的相对可读性，又隐藏了格式细节。

核心矛盾在于如何在保持代码可移植性的前提下，平衡打印语句的简洁性与可读性。原补丁试图用宏彻底解决类型宽度问题，但导致打印语句变得冗长晦涩；Dave Hansen 追求极致简洁但引入非标准格式说明符；David Laight 则主张用轻量级辅助函数在两者间取得平衡。

## 参与讨论人员
- Anshuman Khandual（补丁原作者，邮件的原始回复上下文关联，但未在该子线程中直接发言）
- Dave Hansen (Intel, dave.hansen@intel.com)
- David Laight (david.laight.linux@gmail.com)

## 达成的结论
此次子线程讨论尚未达成明确共识。Dave Hansen 的 `%pT` 方案与 David Laight 的辅助函数方案各有主张，后者的回复发出后尚无进一步响应，讨论仍处于意见交换阶段，没有形成一致的修改方向。

## 下一步改进方向
需要等待补丁作者 Anshuman Khandual 或相关维护者对两种替代方案做出进一步评估。可能的改进方向包括：尝试实现 `%pT` 格式说明符并评估其对内核其他部分的影响；或者采纳 David Laight 的建议，编写简单的本地格式化辅助函数，并在同一补丁系列中保持风格一致。也可以考虑其他更优雅的抽象方式，但核心是需要社区就“抽象打印页表项值的最佳方式”达成共识。另外，需要有人在该邮件线程中继续回复，推动讨论继续。

## 新增补丁
该邮件中未出现新的补丁版本，仅为对当前 RFC V2 补丁的评论和讨论。

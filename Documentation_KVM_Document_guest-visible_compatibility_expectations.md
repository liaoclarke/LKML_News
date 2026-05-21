# Documentation: KVM: Document guest-visible compatibility expectations

---

## 更新 - 2026-05-20 10:47 UTC

## 核心话题
本邮件线程围绕一个旨在明确 KVM 中“客户机可见行为兼容性”预期的文档补丁展开讨论，核心争议点在于：**KVM 在修复模拟硬件中的错误（bug）时，是否应永久保留原有的错误行为以避免对客户机造成破坏**。

Oliver Upton 在回应 David Woodhouse 时明确指出，不应以“假设和可能性”为由要求 KVM 保留所有可能带来客户机可见影响的历史 bug 模拟。他强调：“What ifs and maybes do not meet the bar, in my opinion, for preserving bug emulation in KVM.”（在我看来，“如果”和“也许”并不能成为在 KVM 中保留错误模拟的标准。）他承认可以有一定的灵活性，但必须建立起一套机制，用于区分真正的错误修复与客户机真正依赖的虚拟硬件行为。

David Woodhouse 则持完全相反的立场，他认为一个稳定且成熟的平台不应“随心所欲地给客户机造成破坏”，即便这种破坏源于对原有硬件模拟错误的修正，因为这种修正本身就是一种客户机可见的 ABI 变更。Oliver 对此反驳，认为要求永久保留那些错误模拟，实际上是迫使 KVM 维护者去模拟一种“完全损坏的行为”（emulate something completely broken for you）。

Oliver 进一步指出，这种事后驱动式的审查模式（drive-by scrutiny）是不可接受的工作动态，并质疑对方团队是否已将测试和审查工作建立在主线之上。他表达了对当前协作方式的失望，认为双方始终未能找到一种“富有成效的合作方式”，并请求对方参与到上游代码审查和测试中来，以真正解决问题。邮件的语气反映出维护者对于长期积累的摩擦所感到的疲惫，以及对于原则性问题的坚持。

## 参与讨论人员
- **Oliver Upton** (oupton@kernel.org)：KVM/arm64 维护者，邮件的主要发起回复人。
- **David Woodhouse**：参与讨论的另一方，邮件中被直接回复的对象，据内容推测可能来自下游发行版或客户机内核团队。

## 达成的结论
**未达成共识。** 双方在是否应无条件保留历史错误模拟以保证客户机兼容性这一问题上存在根本性分歧。Oliver 坚持需要有明确标准来过滤哪些 bug 修复是可接受的，拒绝以单纯的可能性作为保留错误行为的理由，并指责对方缺乏建设性的上游参与；David 则坚持认为成熟平台不应强行改变客户机所能观察到的行为（即便该行为源于一个 bug）。邮件对话在质问与对立中结束，未出现任何妥协迹象。

## 下一步改进方向
- **需要明确识别和记录客户机可见行为**：文档补丁正是为实现这一点而提出，但尚需社区（尤其是下游用户）与维护者共同商定哪些 ABI 是可靠的，哪些 bug 修复属于可接受的范畴。
- **改进协作流程**：Oliver 明确要求 David 一方参与主线补丁的审查与日常测试，认为如果能将大量测试落在主线内核上，提前发现问题，远比事后发难更高效。“Maybe it's just me but I am left feeling disappointed that we all haven't found a productive way of working together.”（也许只是我的感受，但我对我们始终未能找到一种建设性的合作方式感到失望。）
- **潜在的折中方案探索**：需要探讨是否引入类似“opt-in”或“quirks”机制，允许用户空间或 VMM 有选择地保留某些历史错误模拟，但此点未在本封邮件中直接提及。

## 新增补丁
本封邮件中未随附任何新补丁版本，仅是对现存补丁 [PATCH] Documentation: KVM: Document guest-visible compatibility expectations 的讨论与立场陈述。

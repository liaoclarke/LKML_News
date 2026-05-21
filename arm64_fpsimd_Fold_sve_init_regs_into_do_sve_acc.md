# arm64: fpsimd: Fold sve_init_regs() into do_sve_acc()

---

## 更新 - 2026-05-21 14:25 UTC

## 核心话题
该补丁来自 Mark Rutland 的 18 补丁系列中的第 5 个，主题是 arm64 的 FPSIMD/SVE/SME 状态管理重构。核心改动是将只被 `do_sve_acc()` 调用的 `sve_init_regs()` 函数直接内联到 `do_sve_acc()` 中，并简化相关注释。Mark 指出，由于历史原因，`do_sve_acc()` 与 `do_sme_acc()` 在结构上不一致——`do_sme_acc()` 直接在函数内部完成了从 FPSIMD 到 SME 的初始化和陷阱关闭，而 `do_sve_acc()` 却把初始化逻辑提取到了外部函数 `sve_init_regs()` 中。这种差异给代码阅读和比对带来了不必要的负担。

内联的 `sve_init_regs()` 负责将任务从 FPSIMD 状态转换为 SVE 状态：清空不与 FPSIMD 共享的 SVE 寄存器部分（即把高位置零），并根据当前状态是在硬件寄存器中（`!TIF_FOREIGN_FPSTATE`）还是在内存中，分别采用直接设置向量长度并冲刷活动寄存器的路径，或更新内存副本的方式。同时还会关闭当前任务在 EL0 执行 SVE 指令时产生的陷阱。Mark 强调此次修改不引起功能性变化，纯粹是为了让 `do_sve_acc()` 的结构与 `do_sme_acc()` 对齐，“making it easier to see similarities and differences”。补丁中仅保留了少量注释来说明转换和陷阱关闭的必要前提（如确保不处于 streaming 模式等）。整体上，这是一次无副作用的清理式重构，目的是提升 arm64 低层陷阱处理代码的可维护性。

## 参与讨论人员
- Mark Rutland (Arm) —— 补丁作者
- Cc 列表中的潜在审核者：
  - Catalin Marinas (Arm)
  - Fuad Tabba (Google)
  - James Morse (Arm)
  - Marc Zyngier (kernel.org, 当时可能仍在 Arm)
  - Mark Brown (kernel.org, 可能就职于 Arm)
  - Oliver Upton (kernel.org, 当时可能就职于 Google)
  - Will Deacon (Arm)

线程中除原始补丁邮件外，无任何回复或讨论，所有 Cc 人员均未发表评论。

## 达成的结论
本邮件线程仅包含补丁提交，无后续讨论。因此未达成任何共识或结论，该补丁尚处于待审查阶段。

## 下一步改进方向
该补丁需在邮件列表上接受维护者和其他开发人员的审查。可能的审查关注点包括：
- 确认内联后没有遗漏原有逻辑（如 TIF_FOREIGN_FPSTATE 检查、向量长度设置、陷阱关闭等），并验证确实无功能性改变。
- 检查简化后的注释是否仍然准确传达了转换的前提条件和副作用，尤其是关于 streaming 模式的断言。
- 讨论是否需要进一步对齐 `do_sve_acc()` 与 `do_sme_acc()` 的其他部分，使两者结构更加一致。
- 如果审查通过，该补丁将随着整个系列合入主线。

## 新增补丁
本邮件即为此补丁的初始版本，为系列 `[PATCH 05/18]` 的一部分。邮件线程中未发布修订版或后续版本。

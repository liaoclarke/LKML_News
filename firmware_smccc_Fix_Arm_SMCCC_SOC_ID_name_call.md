# firmware: smccc: Fix Arm SMCCC SOC_ID name call

---

## 更新 - 2026-05-21 15:18 UTC

## 核心话题
该邮件讨论的是一个针对 ARM SMCCC SOC_ID 名称功能调用的修复补丁。核心问题是：内核通过 SMCCC 调用获取 SoC 人类可读名称字符串时，使用了错误的调用约定函数标识符（FID），导致在符合规范实现的固件（如 TF-A）上永远返回 NOT_SUPPORTED。

补丁作者 Andre Przywara 指出，原先引入该功能的提交（5f9c23abc477）实现的 SOC_ID 名称字符串调用依赖于每个寄存器传输 8 个字符，这在 SMCCC 规范 v1.6 中明确为仅限 AArch64 的功能。因此，对应的 SMCCC 调用必须采用 AArch64 调用约定，需要将 FID 的第 30 位置为 1（即使用 SMC64 调用）。然而，规范文档在参数描述中虽然提到“可选择为 SMC64 调用实现”，但给出的 FID 值仍是 0x80000002，这个值使用的是 SMC32 调用约定（同样适用于另外两个 SOC_ID 子调用）。这就造成了混淆，导致内核实际使用了 0x80000002 作为 FID，而主流 TF-A 实现按照 SMC64 约定期望一个不同的 FID，从而每个调用都返回 NOT_SUPPORTED，SoC 名称功能完全失效。补丁的目的就是修正 FID，使其符合 AArch64 调用约定，修复该功能。

维护者 Sudeep Holla 将此补丁应用到了自己的 sudeep.holla/linux 树的 for-next/ffa/updates 分支，并回复了应用确认邮件。邮件中引用了原始补丁的提交说明，但没有进一步的讨论或争议。

## 参与讨论人员
- Andre Przywara（补丁作者）
- Sudeep Holla（维护者，据邮件地址 sudeep.holla@kernel.org，通常为 Arm 工程师）

## 达成的结论
该补丁已被维护者接受并应用至 sudeep.holla/linux 仓库的 for-next/ffa/updates 分支，即将进入主线。没有出现反对或修改意见，结论明确：补丁正确，修复了 SMCCC SOC_ID 名称调用的 AArch64 调用约定问题。

## 下一步改进方向
补丁已进入维护者分支，下一步通常是等待该分支被上游合入（例如发送 pull request 或直接并入主线的相应子系统树），无需额外修改。如果后续测试发现其他实现也存在类似的 FID 约定冲突，可能需要进一步澄清规范或添加相应的兼容处理，但当前补丁已解决与 TF-A 实现的不匹配问题。

## 新增补丁
- [PATCH] firmware: smccc: Fix Arm SMCCC SOC_ID name call，版本 V1，已应用到 for-next/ffa/updates 分支，对应 commit 70492cfce2a4。

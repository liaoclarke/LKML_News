# drm/msm/a8xx: Fix RSCC offset

---

## 更新 - 2026-05-22 15:41 UTC

## 核心话题
该补丁是修复 Adreno A8xx GPU 系列在 RSCC（可能为 Render State Cache Control 或类似模块）寄存器地址映射上的错误。RSCC 原本被认为是 GMU（Graphics Management Unit）的地址空间的一部分，但实际在 A8xx 架构上，RSCC 模块位于 GPU 自身的寄存器空间内。补丁将 `gmu->rscc` 的虚拟基地址从 `gmu->mmio + 0x19000` 更改为 `gpu->mmio + 0x50000`，并添加注释说明在 a8xx 上 RSCC 位于 GPU 基地址偏移 0x50000 处，属于 `kgsl_3d0_reg_memory` 范围而非 GMU 范围。这直接修复了 commit `50e8a557d8d3 ("drm/msm/a8xx: Add support for A8x GMU")` 引入的错误，很可能导致 A8xx GPU 在电源管理、时钟门控或状态缓存方面的功能异常，因为错误的寄存器地址会导致对 RSCC 的读写完全失效。由于 RSCC 通常与 GPU 的低功耗状态或渲染性能相关，这个偏移错误可能会影响 GPU 的挂起/恢复、动态频率调整等功能。该补丁是系列中的第一枚，后续补丁可能依赖此正确地址进行进一步的 RSCC 初始化或操作。

## 参与讨论人员
- Akhil P Oommen (Qualcomm)

## 达成的结论
该补丁邮件中只有补丁提交，无讨论，因此暂未达成任何共识性结论。补丁仍需社区审核与维护者确认。

## 下一步改进方向
- 等待其他开发者（尤其是 MSM DRM 驱动维护者）对该修复进行审核。
- 验证修复后 A8xx 平台的 RSCC 相关功能是否恢复正常，无副作用。
- 该补丁作为 v5 系列的一部分，可能需结合后续补丁完成完整的 A8xx RSCC 支持修改。

## 新增补丁
此邮件提交的是 `[PATCH v5 1/5]`，即第五版系列补丁中的第一个。邮件内未提供从 v4 到 v5 的变更日志，但版本号表明此前已有多次迭代。

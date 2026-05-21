# iommu/arm-smmu-v3: Allow ATS to be always on

---

## 更新 - 2026-05-20 12:46 UTC

## 核心话题
本邮件讨论的是针对 ARM SMMUv3 驱动的一个改进：允许某些 PCIe 设备的 ATS（地址翻译服务）始终开启。当前驱动在处理设备默认 substream 被绑定到 identity domain 时，会在两种 STE（流表项）模式之间切换：

- **模式 1**：`Cfg=Translate, S1DSS=Bypass, EATS=1` —— 当存在活跃的 PASID（非默认 substream）时使用。
- **模式 2**：`Cfg=bypass`（硬件此时忽略 EATS）—— 当没有 PASID 支持或没有活跃 PASID 时使用。

驱动还会在最后一个活跃 substream 变为非活跃时，将 STE 从模式 1 降级为模式 2。但是，某些 PCIe 设备强制要求 ATS 始终保持开启，此时 STE 必须一直处于模式 1，因为硬件在模式 2 下会忽略 EATS 字段，导致 ATS 无法工作。

该补丁的修改思路是：
1. 始终使用模式 1（`Cfg=Translate, S1DSS=Bypass, EATS=1`）；
2. 永远不降级到模式 2；
3. 即使设备不支持 PASID（即 `ssid_bits=0`），也需要分配并保留一个 CD（上下文描述符）表，以保证 `S1DSS` 字段有效。为此，当 master 要求 `ats_always_on` 时，将 `s1cdmax` 至少设为 1，这样 CD 表会有一个永不使用的虚拟条目（`SSID=1`）。

补丁还调整了 `arm_smmu_cdtab_allocated()` 的判断逻辑：原本对于 identity domain 的默认 substream，第一个 CD 在表中为 NULL 是合法的，但因为引入 `ats_always_on` 后这类设备总是会分配 CD 表，故添加 `!master->ats_always_on` 条件，避免误报未分配。

该补丁由 NVIDIA 的 Nicolin Chen 提交，版本为 v5，已有华为、NVIDIA、Intel 等多个厂商的开发者审查与测试，标签包括 `Reviewed-by`、`Tested-by`、`Acked-by`，表明技术方案已得到多方认可。

## 参与讨论人员
- **Nicolin Chen** (NVIDIA) — 补丁作者
- **Jonathan Cameron** (Huawei) — Reviewed-by
- **Nirmoy Das** (NVIDIA) — Tested-by, Acked-by
- **Jason Gunthorpe** (NVIDIA) — Reviewed-by
- **Kevin Tian** (Intel) — Reviewed-by
- **Dave Jiang** (Intel) — Reviewed-by

（注：本邮件为补丁提交，没有后续讨论回帖，故以上参与者均通过补丁标签体现。）

## 达成的结论
已达成明确共识。该补丁经过多名内核维护者与同行审查、测试，获得了多个 `Reviewed-by`、`Tested-by` 和 `Acked-by` 标签，技术细节已充分论证，方案成熟，等待合入主线。

## 下一步改进方向
- 该补丁（v5 3/3）作为系列的一部分，需与同系列其他补丁协同合入。
- 后续可能由 ARM SMMU 子系统维护者将其纳入 `iommu` 分支，如果存在依赖关系，需提前或一并合入前置补丁。
- 没有提及进一步修改需求，目前无异议，若无新问题应可直接合入。

## 新增补丁
本邮件本身就是补丁提交，属于 v5 版本的系列补丁之第 3 个。与前一版本相比的具体变更未在邮件中详述，但该版本已整合了之前审查意见，并添加了相关审核标签。同系列的前两个补丁未在本邮件中体现，故无法列出完整变更。

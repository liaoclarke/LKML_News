# arm64: mpam: Add memory bandwidth usage (MBWU) documentation

---

## 更新 - 2026-05-20 22:24 UTC

## 核心话题
该邮件是 ARM64 MPAM（Memory Partitioning and Monitoring）功能补丁系列中的一部分，专门为内存带宽使用监控（MBWU）添加用户文档。补丁作者 Ben Horgan 和共同开发者 James Morse 旨在解释通过 resctrl 文件系统向用户空间暴露 MBWU 监控器时的工作机制与限制条件。

技术要点包括：
- 内存带宽监控依赖 MSC（Memory System Component）中的 MBWU 监控器，这些监控器位于 L3 缓存之后或直接位于内存一侧。
- resctrl 使用 L3 缓存的 cache-id 来标识带宽测量点，因此平台必须通过固件提供 L3 缓存的 cache-id（即使平台本身不支持 MPAM 控制，也需要此标识）。
- 如果带宽监控点位于 L3 缓存之后，构成该 L3 组的所有 MSC 上都需要有 MBWU 监控器。若监控点位于内存而非 L3，则要求系统只有一个全局 L3 缓存，否则无法确定流量的来源 L3。
- 暴露 “mbm_total_bytes” 需要 MSC 组拓扑与 L3 缓存拓扑相匹配，以便复用 cache-id。明确举出反例：不具有对应 L3 缓存的 CPU-less NUMA 节点无法暴露 “mbm_total_bytes”。
- “mbm_local_bytes” 不被支持，因为 MPAM 无法区分本地流量与全局流量。

该文档补丁将上述约束清晰地告知用户，帮助系统管理员理解在特定硬件平台上能看到哪些 resctrl 监控文件，以及为何某些文件可能缺失。引用片段：“To expose 'mbm_total_bytes', the topology of the group of MSC chosen must match ... Platforms with Memory bandwidth monitors on CPU-less NUMA nodes cannot expose 'mbm_total_bytes' ... 'mbm_local_bytes' is not exposed as MPAM cannot distinguish local traffic from global traffic.” 这为后续调试和问题报告奠定了基础，补丁中紧接着的 “Reporting Bugs” 章节也提示用户当看不到预期计数器或控制器时，应提供相应信息。

## 参与讨论人员
- Ben Horgan (Arm)
- James Morse (Arm) —— 作为共同开发者（Co-developed-by）署名

## 达成的结论
由于邮件仅为补丁提交，未出现任何回复或讨论，因此未形成明确共识。该补丁作为 v4 系列的一部分，正处于待审状态。

## 下一步改进方向
补丁需要等待社区成员（尤其是 resctrl 和 ARM64 架构维护者）的审查反馈。可能的方向包括：
- 根据审核意见补充或修正文档描述，使其更精确。
- 与系列其他补丁一起进行测试，确保文档与代码行为一致。
- 若有必要，补充更详细的示例或图表以帮助用户理解拓扑限制。

## 新增补丁
- 本邮件即为 [PATCH v4 5/5]，无后续更新版本在此线程中提交。

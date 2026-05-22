# Devicetree support for Glymur GPU

---

## 更新 - 2026-05-22 15:41 UTC

## 核心话题
本邮件线程是 Qualcomm 工程师 Akhil P Oommen 提交的第五版补丁系列，目标是为基于 Glymur 平台的参考设备（CRD）添加 GPU 的 Device Tree 支持。Glymur 芯片搭载了 Adreno X2-85 GPU，属于下一代 Adreno A8x 架构家族，首次在 Adreno 上引入 4 片（slice）架构设计，大幅提升了带宽吞吐能力，最高频率达到 1850 MHz，并加入了光线追踪支持。邮件指出，针对 A8x 全系列 GPU 的电源折叠（IFPC）特性还需要依赖另一个对 gxclkctl/drm 的修改系列，否则 GPU 无法正常工作。

该补丁系列主要包含三部分工作：更新 DT 绑定文档以加入 Glymur GPU 兼容性；添加 GPU SMMU 节点；以及添加 GPU 和 GMU（Graphics Management Unit）本身的节点。一个值得注意的设计决策是故意去掉了 zap shader 固件节点，原因是在 Glymur 笔记本平台上，Linux 可以直接在 EL2 异常级别启动，不再需要通过 zap 固件来授权 GPU 访问，因此该节点被有意遗漏。这是新一代高通平台在固件架构上的一个积极变化，直接简化了主线 Linux 的支持需求。

v5 版本的变更主要响应了审查意见：放宽了 reg-names 属性在绑定中的限制（应 Krzysztof 要求）；同时移除了 SMMU 绑定文档的补丁，因为该部分已被独立收录。该版本基于 v4 改进而来，v4 增加了被动散热支持，v3 则修复了 drm-msm 中 RSCC 基地址虚拟地址问题，并去除了 adreno SMMU 的 interconnect 属性。邮件还特别提到，实际启动设备时，除了该 GPU 系列，还需要一个与 GPU 无关的补丁系列（qref_vote）才能正常运行 linux-next 内核。这体现了高通新一代 GPU 平台上游化的复杂性，涉及时钟、电源、互连、SMMU 等多个子系统之间的依赖关系。核心论点在于：Glymur GPU 作为首款采用 A8x 架构的桌面级/笔记本级 Adreno，标志着高通 GPU IP 向高带宽场景的延伸，其 Device Tree 描述需要如实反映新的切片拓扑、更高的时钟频率以及不需要 zap 固件等特性。

## 参与讨论人员
- **Akhil P Oommen** (Qualcomm) —— 补丁作者与提交者
- **Krzysztof Kozlowski** （推测，邮件中仅提及 “Krzysztof”） —— 在先前版本中提出了绑定文档的审查意见，本版据此进行了修改

## 达成的结论
由于该线程仅有补丁系列的封面邮件，尚未出现任何后续讨论或审查反馈，因此截至目前该版本未达成任何结论。补丁状态为待审核，社区尚未就绑定设计、节点结构或依赖关系给出最终意见。

## 下一步改进方向
1. **社区审查**：等待设备树维护者（如 Rob Herring、Krzysztof Kozlowski）以及 MSM DRM 和维护者对补丁进行审查，重点关注 glymur 绑定是否合理、reg-names 放宽是否符合规范、无 zap shader 节点的说明是否充分。
2. **依赖关系明确化**：补丁依赖的 “gfx clk fixes” 系列需要先被合入，或至少达成一致，确保 IFPC 特性在所有 A8x GPU 上的基础支持到位后，Glymur 的 DT 支持才能生效。
3. **启动测试**：补丁作者提到基于 linux-next 时还需额外的 qref_vote 系列才能启动，这可能意味着 glymur CRD 的参考设备树存在多方面的缺失，需要进一步与平台固件团队对齐，并确保主线内核能在无外部补丁的情况下干净启动。
4. **文档补充**：如果确定 Glymur 平台是首个在 EL2 启动且不需要 zap 固件的 Adreno 平台，可能需要在相关文档或提交日志中说明这一假设，避免未来其他开发者产生混淆。

## 新增补丁
本邮件线程披露了第五版补丁系列：
- **[PATCH v5 0/5] Devicetree support for Glymur GPU**  
  包含 5 个补丁（具体标题未在封面列出），主要变化为：
  - 根据 Krzysztof 的意见放松了 reg-names 的约束条件；
  - 移除了已经独立合入的 SMMU 绑定文档补丁；
  - 前几版已累积的改动：v4 增加被动散热支持，v3 修复 RSCC 基地址及去除 interconnect 属性等。

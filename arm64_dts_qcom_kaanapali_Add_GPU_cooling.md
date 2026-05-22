# arm64: dts: qcom: kaanapali: Add GPU cooling

---

## 更新 - 2026-05-22 19:51 UTC

## 核心话题
本邮件讨论围绕在 Qualcomm 平台的 `kaanapali` 设备树中引入 GPU 主动冷却（cooling）机制。原补丁（PATCH 6/8）意图将 GPU 热管理跳变点类型从 “hot”（热跳变）改为 “passive”（被动跳变），并将温度阈值从 120°C 下调至 105°C，目标是让 GPU 在温度超过 105°C 时主动降频，而非像之前那样等到 120°C 才触发严重过热保护。补丁作者在提交说明中指出：“Unlike the CPU, the GPU does not throttle its speed automatically when it reaches high temperatures.” 即 GPU 与 CPU 不同，缺乏自动频率节制能力，因此需要额外的主动冷却手段。

讨论的核心争议点在于跳变点类型的取舍。Dmitry Baryshkov 审查补丁时提出：“Why don't we keep both passive and hot trip points?” 他认为不应直接删除原有的 “hot” 跳变点，而应同时保留被动（降频）和热（进一步保护）两级跳变点。Gaurav Kohli 最初回复：“Need guidance here, we are keeping passive at low temp so still hot trip is needed for such cases.” 暗示其团队已理解需要保留热跳变点，但措辞略显模糊。经 Dmitry 进一步确认“I think we are saying the same. Keep both passive and hot trip points.”后，Gaurav 明确回应 “Sure, will send updated one.” 表示同意并将发送更新版本。

这段讨论体现了 Linux 内核热管理框架的典型设计原则：通过多级跳变点（如 passive、hot、critical）实现分层温控策略。被动跳变点（passive）允许操作系统通过调节设备性能状态（如 GPU 频率）来降温，而热跳变点（hot）通常用于通知用户空间或触发更紧急的操作。仅保留 passive 可能使得在温度持续上升至更危险水平时缺少相应的硬件保护响应。双方很快达成一致，说明这是一个相对成熟的设计模式，修改方向明确。

## 参与讨论人员
- **Gaurav Kohli** (gaurav.kohli@oss.qualcomm.com) — 补丁作者之一，负责回应与修改。
- **Dmitry Baryshkov** — 审查者，提出保留两级跳变点的关键意见。
- **Akhil P Oommen** (akhilpo@oss.qualcomm.com) — 共同提交者，在补丁中作为 Signed-off-by 出现，但未参与此子线程实际讨论。

## 达成的结论
已达成共识。双方同意在 GPU 热管理区域同时保留 **passive（被动）** 和 **hot（热）** 两种跳变点：passive 跳变点设置在较低温度（105°C）以触发主动降频冷却，hot 跳变点保留在原有较高温度（推测仍为 120°C）作为进一步保护措施。

## 下一步改进方向
Gaurav Kohli 需按共识更新补丁，在 `gpuss-0-alert0` 等跳变点配置中同时加入 `passive` 和 `hot` 两种类型，然后提交新版本（v2）。更新后的补丁需通过邮件列表重新发送以供审查。

## 新增补丁
本邮件子线程中未直接发布新补丁版本，但 Gaurav 明确表示 “will send updated one”，预期后续将发布 v2 版本补丁，包含同时保留被动与热跳变点的修改。

# arm64: dts: qcom: Add GPU support for Glymur

---

## 更新 - 2026-05-22 15:42 UTC

## 核心话题
该邮件为 Linux 内核 ARM64 设备树补丁系列的第 5 版第 4 个补丁，主题是为 Qualcomm 的 Glymur SoC 添加 GPU 支持。Glymur SoC 搭载了 Adreno X2 系列 GPU，属于 A8x 家族，这是 Adreno GPU 的新一代硬件 IP。补丁作者 Akhil P Oommen 指出，这款 GPU 在微架构层面进行了改进，并具有与以往不同的硬件配置参数，例如 GMEM 大小、着色处理器（SP）数量、各级缓存容量等。因此，需要为这个新硬件添加相应的设备树节点和运行点（OPP）表，以支持频率调节和电源管理。

具体的技术实现上，补丁在 `arch/arm64/boot/dts/qcom/glymur.dtsi` 文件中新增了 `gpu@3d00000` 和 GMU（Graphics Management Unit）等节点。GPU 节点的兼容性字符串（compatible）设置为 `"qcom,adreno-44070001"` 和通用的 `"qcom,adreno"`，其中 44070001 是 Adreno A8x 系列中的一个具体芯片标识符。节点包含了寄存器映射（`kgsl_3d0_reg_memory` 和 `cx_mem`）、中断号（GIC_SPI 300）、IOMMU 引用（`adreno_smmu`）、互连（interconnects）带宽配置，以及指向 GMU 的 phandle（`qcom,gmu`）。OPP 表定义了多个频率档位及其对应的电压等级（通过 RPMH 调节器级别表示）、峰值内存带宽（`opp-peak-kBps`）和硬件支持掩码（`opp-supported-hw`），其中注释标明了“ACD 被禁用”。补丁正文中截断的 OPP 描述了从 310 MHz 到更高频率的多个档位，但后续内容被省略。

该补丁还包含了 `Reviewed-by: Konrad Dybcio <konrad.dybcio@oss.qualcomm.com>` 标签，表明已经经过了一次审查。邮件的 diff 片段显示了 183 行新代码被添加，目前限于 GPU 节点的一部分，GMU 节点尚未在片段中展示。整个补丁的主题是为这个尚未正式发布的 Adreno X2 GPU 提供基础设备树支持，后续可能还需要更多补丁来处理 GMU、电源域、时钟控制器等辅助硬件的绑定。

## 参与讨论人员
- Akhil P Oommen, oss.qualcomm.com (补丁作者)
- Konrad Dybcio, oss.qualcomm.com (审核者)

## 达成的结论
由于邮件列表中只出现了这一封邮件，缺乏后续的讨论回复，因此无法判断是否已达成共识。从补丁带有 "Reviewed-by" 标签来看，内部审查已经通过，但尚未在邮件列表上引发进一步的公共讨论或合并请求。目前只能认为该补丁处于待审核、待合并的状态。

## 下一步改进方向
- 需要其他维护者（如 Qualcomm 子系统的维护者或 ARM64 设备树维护者）进行审阅并给出反馈。
- 可能需要提供完整的补丁上下文（当前邮件内容被截断，GMU 节点未完全显示），以确保 GMU 和其他相关节点的定义正确。
- 如果涉及新的 Adreno 固件接口或 GMU 通信机制，还需要确认对应驱动代码是否已就绪，或需对应驱动补丁同时提交。
- 可能需要在多个 Glymur 硬件平台上测试该设备树，确保 GPU 初始化和频率切换等功能正常工作。

## 新增补丁
本邮件即为新增补丁：`[PATCH v5 4/5] arm64: dts: qcom: Add GPU support for Glymur`。这是该系列的 v5 版本第 4 个补丁，在此之前应该还有前 3 个补丁和后续第 5 个补丁。当前补丁的内容是首次添加 Glymur 的 GPU 设备树节点，之前版本是否包含此节点未知，但 v5 表明已经过多次迭代。

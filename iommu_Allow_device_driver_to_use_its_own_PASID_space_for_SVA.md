# iommu: Allow device driver to use its own PASID space for SVA

---

## 更新 - 2026-05-21 15:39 UTC

## 核心话题
本邮件讨论围绕一个针对ARM64架构IOMMU子系统的补丁（v2），其核心目的是解决在特定场景下SVA（Shared Virtual Addressing）功能因全局PASID空间资源竞争而失败的问题。邮件作者Joonwon Kang描述了一个真实环境中的故障：当一台非PCIe设备需要启用SVA，而其硬件支持的SSID/PASID空间极小（仅1到3个），一旦系统中其他模块（如通过`iommu_alloc_global_pasid()`或`iommu_sva_bind_device()`）预先占用了这些少量的PASID，该设备的SVA绑定就会因无可用PASID而失败。

问题的深层原因在于当前IOMMU核心强制使用全局PASID空间，这一设计源于Intel CPU中ENQCMD指令的限制——该指令从和进程绑定的IA32_PASID寄存器中获取PASID操作数，因此一个进程与多个设备通信时无法在内核不介入的情况下为不同设备切换PASID。ARM架构也引入了类似指令ST64BV0，面临相同约束。针对这种硬件无法动态切换的小PASID空间设备，补丁提出允许设备驱动维护自己的私有PASID空间，并通过新API `iommu_sva_bind_device_pasid(dev, mm, pasid)` 显式分配一个驱动指定的PASID来建立进程与设备的绑定。

该方案会带来一个明确的取舍：进程将无法在EL0执行ENQCMD类指令，因为进程自身无法为了不同设备更改IA32_PASID（或ARM的ACCDATA_EL1）中的值。为此补丁设计了互斥约束——同一进程不能混用`iommu_sva_bind_device()`和`iommu_sva_bind_device_pasid()`，并且当前暂不支持一个进程同时对多个设备使用不同PASID进行SVA。邮件中Baolu Lu（Intel）对此进行了回复（内容被截断），表明该方案正在受到IOMMU维护者的评审，讨论集中在如何平衡驱动私有PASID空间与全局ENQCMD兼容性需求之间的冲突。

## 参与讨论人员
- Joonwon Kang（发件人，邮箱未完整显示，应为补丁作者，来自Samsung或其他ARM设备相关厂商）
- Baolu Lu（baolu.lu@linux.intel.com，Intel IOMMU子系统维护者）

## 达成的结论
邮件片段只展示了Baolu Lu的回复起始部分，回复具体内容被截断。从上下文看，讨论尚未达成明确共识，补丁v2仍处于技术评审阶段，主要待解决问题是如何处理私有PASID空间与依赖全局PASID的ENQCMD/ST64BV0指令集之间的互斥语义，以及API设计的完备性。

## 下一步改进方向
- 根据Baolu Lu和其他维护者的反馈，需要明确`iommu_sva_bind_device_pasid()`的适用范围，是否应在IOMMU核心层增加对设备能力的查询，自动判断可否使用私有PASID空间，而非完全由驱动决定。
- 完善对混用不同绑定API的错误处理及内核文档，澄清与ENQCMD相关进程的交互限制。
- 可能需要补充针对ARM SMMUv3驱动层的实现细节，确保PASID分配在硬件极少SSID时的有效性。
- 需要在多种设备、混合全局与私有PASID场景下进行测试，验证不存在恶性竞争或状态泄露。

## 新增补丁
该邮件讨论基于[PATCH v2]，目前未在该片段中看到更新的补丁版本（v3或rfc v2）发布。若后续讨论产生实质性改动，预计作者会发布v3补丁。

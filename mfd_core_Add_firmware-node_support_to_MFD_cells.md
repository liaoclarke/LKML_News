# mfd: core: Add firmware-node support to MFD cells

---

## 更新 - 2026-05-21 15:36 UTC

## 核心话题
该讨论围绕为MFD（多功能设备）核心添加固件节点（firmware-node）支持展开，具体涉及补丁v22系列中的第08个补丁。其核心动机是解决当MFD子设备在设备树（Device Tree）中缺乏兼容字符串（compatible string）时，如何正确关联固件节点的问题。典型场景例如PSCI的“reboot-mode”节点，它仅描述底层固件提供的启动状态，并不包含兼容字符串，导致MFD核心无法通过常规的OF匹配机制（基于compatible）为子设备分配合适的fwnode。

补丁原始方案是在`struct mfd_cell`中增加一个回调函数（callback），允许驱动显式提供固件节点。注册子设备时，如果设备树、ACPI或软件节点均未分配fwnode，则调用此回调获取节点并附加到子设备上。具体实现中，在`mfd_add_device()`函数内增加了`struct fwnode_handle *fwnode`变量，并利用`mfd_child_fwnode_put()`作为释放回调，通过`devm_add_action_or_reset()`管理生命周期。

讨论的核心技术争执在于回调函数的必要性。Bartosz Golaszewski首先提出，或许可以用更简单的字段替代回调，例如在`mfd_cell`中添加`const char *cell_node_name;`。如果设置了该字段，MFD核心会直接根据名称查找父设备固件节点下的子节点，而不是让驱动提供回调。Lee Jones进一步质疑为何不能让子设备自行查找其fwnode，认为设备自己查找节点似乎更直接。Bartosz回应称，尽管子设备可以自行查找，但逻辑上并不合理——让子设备在已经挂载到驱动后，再回溯父节点并自行分配fwnode，破坏了层次结构的清晰性，这类工作应当在子系统层面、设备注册之前完成。这段对话反映出维护者对实现方式的原则性考量：fwnode的分配应该由核心层集中处理，避免分散到各个驱动中，从而保持框架的整洁。

此外，截断的邮件中还提到了`mfd_child_fwnode_put()`函数的定义，但Lee Jones似乎对某个前置问题有所疑问，文本被截断未能完整呈现。

## 参与讨论人员
- **Shivendra Pratap** <shivendra.pratap@oss.qualcomm.com>：补丁作者，来自Qualcomm开源组织。
- **Bartosz Golaszewski** <bartosz.golaszewski@oss.qualcomm.com> / <brgl@kernel.org>：补丁的建议者，同样来自Qualcomm，对实现方式提出改进意见。
- **Lee Jones** <lee@kernel.org>：MFD子系统维护者，对补丁进行审查并提出架构层面的追问。

## 达成的结论
该讨论并未达成最终共识。Bartosz虽然愿意接受回调方案（“I suggested it because of its flexibility”），但同时也提出了更简单的`cell_node_name`备选方案，并未明确否决任一方式。Lee Jones质疑子设备自寻fwnode的可能性，Bartosz则解释了由核心层处理的必要性。从现有邮件片段看，究竟采用回调、字段还是其他方式仍未确定，需要进一步讨论或下一版补丁来明确。

## 下一步改进方向
根据讨论，后续可能的改进方向包括：
1. 评估是否采用`const char *cell_node_name`字段替代回调，减少灵活性但简化了驱动实现和核心代码。
2. 补丁作者Shivendra需要回应Lee Jones的疑问，澄清为什么子设备自行查找fwnode不适用，并阐述在核心层集中处理的优势。
3. 若维持回调方案，可能需要补全相关代码注释或文档，阐明回调的使用时机和限制。
4. 本补丁是系列的一部分，还需确保与后续补丁（如利用此机制的PSCI reboot-mode实现）协同一致，待整体方案确认后提交新版本。

## 新增补丁
在本邮件线程中未发布新的补丁版本，仍为v22 08/13。讨论停留在审查反馈阶段，预计在达成一致后会有v23更新。

---

## 更新 - 2026-05-21 17:27 UTC

## 核心话题
本讨论围绕在 MFD（多功能设备）核心层为 MFD cell 添加固件节点（firmware node）支持的补丁展开，属于 v22 版本系列中的一个补丁。背景是针对 ARM64 平台下某些 MFD 设备，其子设备在设备树中可能不存在标准的 compatible 属性，因此需要一种机制让 MFD 子设备（cell）能够正确关联到父设备固件节点下的对应子节点，以便后续驱动能获取到所需的配置信息（如资源等）。

讨论的焦点是具体实现方式。Bartosz Golaszewski 提出了一种折中方案：在 `mfd_cell` 结构体中新增一个 `cell_node_name` 字段，若该字段被设置，则 MFD 核心层会在注册子设备前，通过名称在父设备节点的子节点中查找对应的固件节点，并将其赋给 cell。他在邮件中解释：“I suggested it because of its flexibility. The alternative I had in mind is something like a new field in mfd_cell: const char *cell_node_name; Which - if set - would tell MFD to look up an fwnode that's a child of the parent device's node by name - as it may not have a compatible.” 这表明，因为子节点可能没有 compatible 属性，简单的 compatible 匹配不可行，所以采用名字查找更灵活。

Lee Jones 则质疑为何不能让子设备驱动自行查找自己的固件节点，他问道：“Remind me why the chlid device can't look-up its own fwnode?” 对此，Bartosz 回应，技术上子设备确实可以自行查找，但从软件分层逻辑上看并不合理：“Oh sure it can, but should it? I'm not sure it's logically sound to have the child device reach into the parent, look up the fwnode and then assign it to itself after it's already attached to the driver. This should be done at the subsystem level before the device is registered.” 他主张这种 fwnode 的绑定应在子系统层面完成，即在设备注册给驱动之前就设置好，以避免驱动自行侵入父设备内部进行查找，这样更符合职责分离原则。

Lee Jones 最后的反驳 “Leaf drivers reach back into the parent all the time.” 则指出在内核中，叶子设备驱动访问父设备是十分常见的做法，言下之意是这种“自行查找”并非异常，可以接受。由此，讨论陷入了子系统集中处理与驱动自主处理的灵活性和惯例之争。

## 参与讨论人员
- Lee Jones (lee@kernel.org)，内核 MFD 子系统维护者
- Bartosz Golaszewski，补丁作者（或重要评审者，具体公司未在邮件中注明）

## 达成的结论
本轮讨论未形成明确共识。Lee Jones 认为叶子驱动自行向父设备查找 fwnode 是常见且可接受的模式，而 Bartosz Golaszewski 坚持认为在子系统层统一处理在逻辑上更优。双方尚未就补丁的具体实现方式达成一致。

## 下一步改进方向
需要就 fwnode 分配方案进一步讨论，决定是采用在 `mfd_cell` 中添加新字段由 MFD 核心统一查找，还是接受子设备驱动自行查找的方式。若采用新字段方案，需更新补丁并说明其相较于驱动自行查找的优势；若采用驱动自行查找，则现有补丁可能需要简化为仅提供辅助接口，或由各设备驱动分别实现。此外，可能还需更多 ARM64 平台 MFD 驱动维护者参与讨论以保证方案的通用性。

## 新增补丁
本邮件仅是对 v22 版本补丁（PATCH v22 08/13）的讨论，该线程中未发布新版本补丁。

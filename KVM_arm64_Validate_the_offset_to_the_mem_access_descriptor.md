# KVM: arm64: Validate the offset to the mem access descriptor

---

## 更新 - 2026-05-20 20:49 UTC

## 核心话题
该补丁是 KVM/arm64 pKVM（受保护 KVM）中处理 FF-A（Arm 的固件框架）内存共享事务的安全加固。背景是：当虚拟机通过 FF-A 协议请求共享或捐赠内存时，hypervisor 的 EL2 代码（位于 `arch/arm64/kvm/hyp/nvhe/ffa.c`）需要解析来自客户机的内存区域描述符。描述符结构包含一个内存区域头部（`ffa_mem_region`），以及随后的一个或多个端点内存访问描述符（EMAD）。在 FF-A 1.1 标准引入 `ep_mem_offset` 字段之前，传统实现默认 EMAD 紧跟在头部之后，这样恶意或出错的客户机可以通过构造畸形的内存区域声明，导致 hypervisor 解析时访问越界。

补丁的描述明确指出：“Prevent the pKVM hypervisor from making assumptions that the endpoint memory access descriptor (EMAD) comes right after the FF-A memory region header.” 引入的修复在 `__do_ffa_mem_xfer()` 中增加了边界检查：首先计算出 EMAD 在共享缓冲区中的偏移量 `em_mem_access_off`（通过 `ffa_mem_desc_offset()` 函数，该函数会根据 FF-A 版本返回适当的偏移），然后判断 `em_mem_access_off + sizeof(struct ffa_mem_region_attributes)` 是否超过实际从客户机传过来的有效数据长度 `fraglen`。若超界，则立即返回 `FFA_RET_INVALID_PARAMETERS` 错误，并释放 RX 缓冲区。这一改动消除了接收路径上对客户机输入数据布局的任何隐含假设，显著提高了 pKVM 在处理 FF-A 内存事务时的健壮性。

邮件中特别注明了本次 v4 补丁相对于之前版本的变化：“[@Mostafa, Add missing call to ffa_rx_release() and use fraglen as the max buffer size as it is the only intialised part]”。这表明早期版本可能遗漏了在错误路径中调用 `ffa_rx_release()` 释放收发缓冲区，且最初使用的缓冲区长度上限 `len` 可能不准确（`fraglen` 才是已初始化的有效数据长度），v4 一并修正了这两处问题。代码片段中 `em_mem_access_off + sizeof(struct ffa_mem_region_attributes) > fraglen` 正是最核心的安全校验，后续的代码逻辑会在此基础上安全地访问 EMAD。

## 参与讨论人员
- Mostafa Saleh <smostafa@google.com>（Google）
- Sebastian Ene <sebastianene@google.com>（Google，原补丁作者）

## 达成的结论
该邮件仅为补丁提交（[PATCH v4 5/5]），未包含来自其他开发者的反馈、评审意见或讨论，因此未形成任何实质性的结论或共识。补丁自身提出了一个明确的安全加固方案，尚待社区审核。

## 下一步改进方向
- 等待 Linux KVM/arm64 维护者或持续审查者（如 Marc Zyngier、Oliver Upton 等）的代码审查与反馈。
- 可能需要补充更详细的提交日志，说明该越界访问在实际攻击场景中的可利用性，以凸显补丁的必要性。
- 如果审查通过，则按流程合入 kvmarm 或主线内核树的相应分支。
- 如有进一步讨论，可能涉及对 `ffa_mem_desc_offset()` 的版本兼容性更细致的设计，或统一 `len`/`fraglen` 的用法。

## 新增补丁
本邮件即补丁 v4 版本，属于系列 `[PATCH v4 0/5]` 中的最后一封（5/5）。该版本的更新内容（与 v3 相比）为：补充了缺失的 `ffa_rx_release()` 调用；将边界检查中的最大缓冲区长度从 `len` 改为 `fraglen`，因为后者才是当前已实际从客户机拷贝的有效数据部分，确保检查更加精确。

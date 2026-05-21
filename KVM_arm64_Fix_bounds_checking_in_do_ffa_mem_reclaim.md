# KVM: arm64: Fix bounds checking in do_ffa_mem_reclaim()

---

## 更新 - 2026-05-21 13:12 UTC

## 核心话题
本邮件串讨论的是 Linux 内核 KVM/arm64 中 pKVM 处理 FF-A 内存回收请求时的一个边界检查缺陷修复补丁。补丁作者 Mostafa Saleh 指出，虽然 pKVM 信任安全分区管理器(SPMD)，但仍需对 SPMD 返回的数据做基本校验。原有检查仅判断偏移量 `offset > len`，但即使 `offset < len`，在随后的 `ffa_host_unshare_ranges()` 中仍可能因地址范围计数 `addr_range_cnt` 导致越界写入。修复方案将单一检查拆分为两步：  
1. 检查描述符中固定部分是否越界（`offset + CONSTITUENTS_OFFSET(0) > len`）；  
2. 在获取 `reg` 后，进一步检查可变数组大小（`addr_range_cnt`）是否适配剩余长度。

这里 Marc Zyngier 提出了一个关键性质疑：**该修补仍然使用 `WARN_ON()`，而在大多数 pKVM 配置下这会导致内核 panic**。Marc 暗示，即使检查更加精确，以 panic 方式应对 SPMD 返回的无效数据或许过于严厉，可能造成不必要的系统崩溃。Mostafa 则询问哪种配置下会实际触发这个检查，以及当前的代码是否已对头部进行越界访问，试图厘清问题的实际严重性。随后的邮件中 Marc 的回复被截断，但从上下文推断双方正在探讨是否应采用更温和的错误处理方式（例如仅返回错误码），而非直接使用可能引发 panic 的 `WARN_ON`。

## 参与讨论人员
- Marc Zyngier (maz@kernel.org)
- Mostafa Saleh (smostafa@google.com)

## 达成的结论
尚未达成明确结论。讨论停留在是否应将 `WARN_ON` 替换为不触发 panic 的错误处理，以及确认当前是否存在实际的越界风险。双方就 `WARN_ON` 的适用性存有分歧，没有做出最终决定。

## 下一步改进方向
1. 评估在 pKVM 不同配置下该检查被触发的实际可能性及影响，明确是否需保留可能导致 panic 的 `WARN_ON`。  
2. 若确认 `WARN_ON` 过于严厉，需修改错误处理路径，例如改为返回 `-EINVAL` 并安全退出，避免因 SPMD 的无效数据导致宿主机崩溃。  
3. 可能需要重新发送补丁版本，将 `WARN_ON` 替换为更合理的错误处理，并确保修复仍能防止越界访问。

## 新增补丁
本邮件串中未发布新版本补丁，仅对 v4 版本的一个 patch 进行评审讨论。

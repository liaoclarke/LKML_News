# dma-direct: rename ret to cpu_addr in alloc helpers

---

## 更新 - 2026-05-22 09:58 UTC

## 核心话题
该补丁是 ARM64 架构相关 DMA 直接映射系列重构（v5）中的一个清理性补丁，目标是对 `kernel/dma/direct.c` 中 `dma_direct_alloc()` 和 `dma_direct_alloc_pages()` 两个函数的局部变量进行重命名，将原本含义模糊的 `ret` 改为语义明确的 `cpu_addr`。补丁作者 Aneesh Kumar K.V 指出，这两个函数中的 `ret` 实际保存的是“返回的 CPU 映射地址”，而非通用的返回值或错误码，因此原名容易让阅读者误解其用途，增加了代码的理解成本。重命名后使分配路径的逻辑更加清晰，并与变量实际表示的含义保持一致。

从补丁内容来看，修改仅限于变量声明及所有引用处的替换，例如在分配连贯映射（coherent mapping）时：
```c
-		ret = dma_common_contiguous_remap(page, size, prot, __builtin_return_address(0));
+		cpu_addr = dma_common_contiguous_remap(page, size, prot, __builtin_return_address(0));
```
以及在直映射或设定 uncached 属性时：
```c
-		ret = page_address(page);
+		cpu_addr = page_address(page);
-		uncached_cpu_addr = arch_dma_set_uncached(ret, size);
+		uncached_cpu_addr = arch_dma_set_uncached(cpu_addr, size);
```
这种变动没有改变任何功能逻辑，纯粹是代码可读性的提升。该补丁作为系列的第 14/20 个补丁，表明整体系列很可能在重构 DMA 直接分配接口，为后续引入新特性（如对 ARM64 某些内存属性更细粒度的控制）做铺垫，而局部变量的正确命名有助于后续补丁的理解和审查。

## 参与讨论人员
- **Aneesh Kumar K.V (Arm)** —— 来自 Arm 公司，邮箱 aneesh.kumar@kernel.org，本补丁的提交者。

## 达成的结论
该邮件线程仅包含补丁提交本身，无任何后续回复、审查意见或讨论。因此无法判断社区是否已对此变更达成明确共识。通常情况下，此类纯重命名、无功能影响的清理补丁争议较小，多数维护者会直接接受，但由于缺少公开反馈，暂不能明确结论。

## 下一步改进方向
- 需要相关子系统的维护者（如 DMA 映射维护者 Christoph Hellwig 等）对该补丁进行审查。
- 补丁作为系列的一部分，需要考察其与前后补丁的依赖关系，确保合入时系列整体可干净应用。
- 若无反对意见，预计该补丁将随系列后续版本或最终版本整合进入主线。

## 新增补丁
本线程未发布补丁的新版本，仍为 `[PATCH v5 14/20]`。

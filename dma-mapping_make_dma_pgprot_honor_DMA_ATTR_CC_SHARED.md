# dma-mapping: make dma_pgprot() honor DMA_ATTR_CC_SHARED

---

## 更新 - 2026-05-22 09:58 UTC

## 核心话题
本邮件是 Aneesh Kumar K.V 针对 ARM64 架构（及其他架构通用 DMA 映射层）提交的补丁，属于其机密计算相关补丁系列的第 8 个 patch（v5）。核心目的是重构 DMA 映射核心的页表属性选择逻辑，将加密／解密（encrypted/decrypted）的 pgprot 处理统一收敛到 `dma_pgprot()` 函数内部，消除调用者的开放编码（open‑coded）判断，从而使 DMA API 能更简洁地支持机密计算下的共享（CC Shared）内存需求。

作者在补丁描述中指出：“Fold encrypted/decrypted pgprot selection into dma_pgprot() so callers do not need to adjust the page protection separately.” 即把原本分散在调用路径中的“是否需要解密”判断，内聚到 `dma_pgprot()` 中，通过新增对 `DMA_ATTR_CC_SHARED` 属性的检查来实现。具体来说，当该属性被置位时，表示 DMA 缓冲区应当以解密（非加密）方式映射，此时 `dma_pgprot()` 会调用 `pgprot_decrypted()`；否则默认调用 `pgprot_encrypted()`（对应于机密计算环境需要保持加密的情况）。补丁对 kernel/dma/direct.c 中的两条关键路径进行了改造：

1. **dma_direct_alloc() 的 remap 路径**：删除了原先对 `force_dma_unencrypted()` 的显式检查以及随后的 `pgprot_decrypted()` 调用，直接让 `dma_pgprot()` 根据属性自行处理。这使分配路径更干净，并将机密安全决策集中在 DMA 属性层。
2. **dma_direct_mmap() 路径**：原先代码在调用 `dma_pgprot()` 后再次通过 `force_dma_unencrypted()` 判断并手动解密页表属性，现在改为在调用前为属性集添加 `DMA_ATTR_CC_SHARED`，然后将整个 attrs 传入 `dma_pgprot()`，由后者统一调整 `vm_page_prot`。这种改动避免了在 mmap 路径中出现重复的、不一致的解密逻辑。

diff 中关键的代码转变显示，作者在 dma_direct_mmap() 中写道：
```
-	vma->vm_page_prot = dma_pgprot(dev, vma->vm_page_prot, attrs);
 	if (force_dma_unencrypted(dev))
-		vma->vm_page_prot = pgprot_decrypted(vma->vm_page_pro

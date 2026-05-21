# arm64: RMI: Configure the RMM with the host's page size

---

## 更新 - 2026-05-21 15:53 UTC

## 核心话题
本邮件讨论围绕ARM64架构下RMM（Realm Management Monitor）的配置补丁展开，具体为v14系列补丁的第07/44个。补丁目标是利用RMM v2.0引入的新特性——允许主机侧通过RMI接口配置RMM内部使用的粒度大小（granule size）。当前主机内核页面大小可能是4KB、16KB或64KB，补丁通过检查特征寄存器并向RMM下发配置命令，使RMM的粒度与主机页面大小对齐，从而让后续的RMI操作能以PAGE_SIZE为粒度进行，简化设计并提升效率。Steven Price提交的补丁在`arch/arm64/kernel/rmi.c`中新增`rmi_configure()`函数，通过`rmi_rmm_config_set`调用完成配置。补丁中先申请一页内存作为`rmm_config`结构体，根据`PAGE_SIZE`填充`rmi_granule_size`字段，然后调用RMI命令。  

Marc Zyngier在审阅中指出两个代码质量问题：  
1. 使用`__free(free_page)`清理属性时，先初始化为`NULL`再赋值是一种容易出错的模式，虽然当前不影响正确性，但未来可能引入bug，建议直接在定义时赋值，避免这种两步初始化。  
2. 针对`PAGE_SIZE`的`switch`语句，ARM64支持的页面大小只有4K、16K、64K三种，`default`分支永远不会被执行，属于死代码。Marc建议用`BUILD_BUG_ON()`在编译期检查意外值，去掉运行时的错误处理。  
此外，邮件末尾截断处显示出对`rmi_rmm_config_set`返回值的进一步疑问（"What is t..."），可能涉及错误处理或返回值的正确性。  

Suzuki K Poulose回复引用了Marc的邮件并继续讨论，但内容被截断，未显示出更多实质性的技术争论点。由于邮件内容不完整，无法确定是否还涉及其他架构层面的考量，但上述两点代码风格/内核规范问题是本片段中明确的改进点。

## 参与讨论人员
- Steven Price (steven.price@arm.com) —— 补丁作者  
- Marc Zyngier (maz@kernel.org) —— 审查者  
- Suzuki K Poulose (suzuki.poulose@arm.com) —— 参与者

## 达成的结论
由于邮件线程被截断，未见Steven Price对Marc Zyngier意见的回应，因此本片段中未达成明确结论。Marc提出了具体的代码修改要求（修正`__free`初始化顺序、用`BUILD_BUG_ON`替换死代码），这通常会被补丁作者接纳。但从现有信息看，尚需等待作者更新或进一步讨论。

## 下一步改进方向
1. **修复`__free`使用模式**：将`struct rmm_config *config __free(free_page) = NULL;`改为直接初始化为`get_zeroed_page(GFP_KERNEL)`，或采用其他无中间NULL状态的写法，避免潜在的清理逻辑错误。  
2. **优化页面大小处理**：用`BUILD_BUG_ON(PAGE_SIZE != SZ_4K && PAGE_SIZE != SZ_16K && PAGE_SIZE != SZ_64K);`代替`default`分支，去除不可达的运行时错误处理代码。  
3. **澄清返回值处理**：Marc在邮件截断处询问“What is t...”，可能涉及`rmi_rmm_config_set`返回值的处理或错误码的转换，需作者补充说明或改进逻辑。  
4. 待补丁作者回复并发布修正版本（v15或后续迭代）。

## 新增补丁
本邮件线程中未出现任何新版补丁，仅涉及对v14补丁的审阅意见。

# kselftest/arm64: Add test for atomic futex uaccess with POE

---

## 更新 - 2026-05-21 10:42 UTC

## 核心话题
本邮件讨论的是为ARM64架构的POE（Permission Overlay Extension，权限覆盖扩展）功能添加一个新的kselftest内核自测用例。补丁作者Kevin Brodsky提交了一个针对"linux kernel mailing list"的补丁，主题为"Add test for atomic futex uaccess with POE"。

这个补丁的核心技术背景涉及ARM64的POE特性和futex（快速用户空间互斥锁）操作之间的交互。POE允许在EL0（用户态）通过POR_EL0寄存器对内存访问施加额外的权限覆盖，类似于x86的pkey（保护密钥）机制。然而，在没有FEAT_LSUI（Load/Store Unprivileged Instructions，非特权加载/存储指令）硬件特性支持的系统中，由FUTEX_WAKE_OP等futex操作触发的原子futex uaccess操作，底层使用的是特权原子加载/存储指令（privileged atomic load/store instructions）。

关键的技术矛盾点在于：因为这些操作使用了特权指令，它们不应该受到用户权限覆盖（POR_EL0）的影响。但如果内核在EL1（内核态）启用了POE，就需要确保PIR_EL1寄存器没有被错误地配置为应用内核覆盖（POR_EL1），否则对于非零pkey的内存映射，futex操作将会失败。

作者特别指出了一个严重的潜在问题："if such misconfiguration occurs, futex_wake_op() may get stuck in an infinite loop because futex_atomic_op_inuser() will fail but fault_in_user_writeable() will still report success." 翻译过来就是：如果发生这种错误配置，futex_wake_op()可能会陷入无限循环，因为futex_atomic_op_inuser()会执行失败，但fault_in_user_writeable()仍然会报告成功（因为从缺页角度看该内存是可写的，只是权限覆盖导致原子操作失败）。这在内核中是一个死循环/活锁bug。

该补丁通过添加一个新的测试文件poe_futex.c来检测这种潜在的内核错误配置。测试会使用非默认的POIndex/pkey映射内存，然后在该内存上执行原子futex uaccess操作，验证操作是否成功。这可以帮助内核开发者在修改POE相关代码时及早发现这类问题。

## 参与讨论人员
*   **Kevin Brodsky** (Arm): 补丁作者，来自arm.com。

## 达成的结论
这是一个单一补丁提交（PATCH 2/2），从提供的邮件内容看，该线程目前只有Kevin的初始补丁提交，没有其他开发者的回复或讨论。因此，尚未形成任何讨论结论或共识。

## 下一步改进方向
由于这只是补丁系列的其中一部分（标记为2/2），且目前未有其他人回应，下一步可能的改进方向包括：
1.  等待社区（尤其是ARM64架构维护者和POE相关开发者）审查此补丁。
2.  测试该新添加的`poe_futex`自测用例能否正确检测出所述的内核错误配置。
3.  确保该测试在支持POE的平台和不支持POE的平台上都能正确skip或通过。
4.  需要考虑将该测试集成到构建系统中（补丁已包含了Makefile修改，将"poe"添加到ARM64子目标中）。
5.  如果内核代码中存在此错误配置，需要提交相应的内核修复补丁，而这个自测可以用来验证修复是否生效。

## 新增补丁
本邮件提供了一个新补丁版本：
*   **[PATCH 2/2] kselftest/arm64: Add test for atomic futex uaccess with POE** (Kevin Brodsky): 这是该补丁系列的第二部分，新增了`poe_futex`测试程序及其相关的Makefile和.gitignore配置。

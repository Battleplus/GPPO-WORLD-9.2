# D-02：冻结策略的只读 latent 诊断

状态：in_progress。正式 T-00～T-05 证据保持不变。

目标：定位 latent 是否改变合法动作分布、同一 checkpoint 内的动作选择、value 和回退路径；诊断开关必须不影响真实执行。

执行前冻结配置见 [protocol.json](protocol.json)。使用 9 个已有 50k checkpoints，在新生成的 12 条开发事件带上各运行 probe-on/probe-off；共 108 对、216 episodes。CPU 仅用于开发诊断，不复刻正式 GPU 性能实验。

必须区分同一策略中共同训练过的 base 分支与独立 GPPO 对照：前者用于量化 adapter 的即时作用，不能作为“移除世界模型后重新训练”的对照。

若开关配对不一致、安全计数非零或哈希变化，保留失败尝试并停止扩大实验。新开发带明确标为开发数据，不能在未来改称未见 Test。T-06 和新训练不在本节点执行范围内。

# S3：必要训练决策与公平对照

S3 已完成必要性审查，选择路径 A：当前限定的三类型基础交付不需要新增训练，因此阶段状态为 `skipped`，不是 `passed`。保留已核验的 S1-R2 checkpoint，接入 S2 的推理上下文优化到实际 M-09 复现入口，并在服务器完成一次新鲜 60-tape 冒烟。

本阶段没有启动训练、没有改变模型权重、没有开展普通 PPO/两类型/五类型/GPPO-History 对照，也没有进入 S4。

主要证据：

- [training-necessity.md](training-necessity.md)：八项必要性审查与路径决定；
- [deployment-candidate.json](deployment-candidate.json)：汇报候选、源码/补丁/模型/配置哈希；
- [fresh-smoke-summary.json](fresh-smoke-summary.json) 与 [fresh-smoke-trace.json](fresh-smoke-trace.json)：服务器新鲜复现；
- [server-evidence.json](server-evidence.json)：服务器资源、命令、归档和下载核验；
- [final-report.md](final-report.md)：可声明范围、限制和 S4 启动条件。

S1-R2 的固定 60 条工程验收与 S2 性能证据继续作为历史/前置证据引用；本阶段的新鲜冒烟单独保存，不把它包装成新的泛化测试集。

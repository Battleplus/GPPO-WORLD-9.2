# J-01 Graph-JEPA v0.1.0

独立的一步动作条件 Graph-JEPA 探索实验已完成，预设接入门槛未通过。未替换 GPPO/EAWM，未启动 JEPA-GPPO 或 T-06。

- 9 次固定预算训练（3 组 × 3 seed），另有 3 个随机表示对照；每次训练 60 epochs / 660 updates。
- 全新数据 112 条事件带、336 episodes、1,325 transitions；保留原始图节点、边、动作与版本。
- 动作敏感性通过，但未来预测不如持久化基线；统一探针相对无动作改善 4.65%，相对监督图对照误差比为 1.873。
- 72 项测试通过；24 个模型/探针哈希、4,044 条逐转移指标及 tape 聚类动作区间已复核。

Assets:

- `j01-dataset.tar.gz`：完整 Train/Validation/Test JSONL、112 条 tape、行为采样器 checkpoint、数据清单与审计。
- `j01-models-and-results.tar.gz`：12 个模型 checkpoint、12 个冻结探针、训练历史、选择封存、逐转移评估与核验。
- `j01-release-inventory.json`：每个归档及每个成员文件的字节数和 SHA-256。
- `j01-results.json`：可直接读取的完整聚合结果。
- `SHA256SUMS.txt`：下载后验证清单。

计划先发布于 `a391544`，数据采集代码 `b566444`，实际训练代码 `4b202e5`。CPU 探索环境，不声称复现旧 T-05 正式 GPU 运行结果或官方视频 JEPA。

报告与下一步：[实验报告](https://github.com/Battleplus/GPPO-WORLD-9.2/blob/main/nodes/J-01/evidence/final-report.md) / [J-02 草案](https://github.com/Battleplus/GPPO-WORLD-9.2/blob/main/nodes/J-02/README.md)。

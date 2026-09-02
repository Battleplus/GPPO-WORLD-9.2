# GPPO-WORLD-9.2

GPPO 世界模型迁移的设计、执行节点与证据索引。

本仓库以 GPPO-8.29 的 [`2a9bb9f`](https://github.com/Battleplus/GPPO-8.29/commit/2a9bb9f87b9d543df144f4d108ba970c924151f9) 设计基线为准，目标是在**不替代 GPPO、不修改真实 belief/action mask、不绕过 ACK/lease/fencing**的前提下，构建动作条件、事件感知的异构图世界模型。

## 当前结论

- 动作空间由系统定义，具体合法动作仍由 GPPO 自主选择。
- 世界模型输入历史可见 belief 图、实际执行动作和已到达证据，预测动作后果。
- 自动事件、Event Predictor 与 GES 用于训练更有效的 latent；默认不把 event logits 直接送入 actor。
- 首阶段只允许冻结的世界模型 latent 作为可关闭的 GPPO 上下文。
- 只有单步预测、校准和安全门禁通过后，才允许研究 1～3 步 imagined rollout。

## 设计入口

1. [范围、分工与安全边界](docs/00-scope-and-boundaries.md)
2. [架构与数据合同](docs/01-architecture-and-contracts.md)
3. [T-00～T-06 执行规划](docs/02-execution-plan.md)
4. [节点、checkpoint 与证据保存规范](docs/03-checkpoint-and-evidence-policy.md)
5. [实验矩阵与验收定义](docs/04-experiment-and-acceptance.md)
6. [节点总索引](nodes/README.md)

## 保存节点

| 节点 | 名称 | 当前状态 | 进入下一节点的门禁 |
|---|---|---|---|
| [T-00](nodes/T-00/README.md) | 基线与数据合同冻结 | passed | schema、白名单、基线清单可复现 |
| [T-01](nodes/T-01/README.md) | 覆盖性轨迹采集 | passed | 严格切分、覆盖报告、数据哈希齐全 |
| [T-02](nodes/T-02/README.md) | Graph World Model 基线 | planned | 独立保存/加载与一步预测通过 |
| [T-03](nodes/T-03/README.md) | 自动事件、Event Head 与 GES | blocked_by_T-02 | WM/EA-noGES/EAWM 公平消融完成 |
| [T-04](nodes/T-04/README.md) | Shadow 与校准 | blocked_by_T-03 | 不改决策、安全回退与校准门禁通过 |
| [T-05](nodes/T-05/README.md) | 冻结 latent 接入 GPPO | blocked_by_T-04 | 可关闭、旧 checkpoint 兼容、无安全退化 |
| [T-06](nodes/T-06/README.md) | 1～3 步 imagined rollout | blocked_by_T-05 | 独立测试增益且安全不变量保持 |

机器可读状态见 [`nodes/status.json`](nodes/status.json)。状态只能在节点证据齐全后由 `planned/blocked` 更新为 `in_progress/passed/failed`；不得用计划文件冒充训练结果或 checkpoint。

## 来源

- [世界模型任务目标与改进目标](https://github.com/Battleplus/GPPO-8.29/blob/2a9bb9f87b9d543df144f4d108ba970c924151f9/docs/world-model/current/%E4%B8%96%E7%95%8C%E6%A8%A1%E5%9E%8B%E4%BB%BB%E5%8A%A1%E7%9B%AE%E6%A0%87%E4%B8%8E%E6%94%B9%E8%BF%9B%E7%9B%AE%E6%A0%87.md)
- [GPPO-8.29](https://github.com/Battleplus/GPPO-8.29)
- [EAWM 官方实现](https://github.com/MarquisDarwin/EAWM)

## 能力声明

当前仓库保存的是设计规划、节点模板和验收合同，**尚不代表世界模型代码、训练、checkpoint 或实验结论已经完成**。真实产物必须按证据规范登记 SHA-256、来源提交、配置、seed、数据切分和指标。

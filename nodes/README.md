# 节点总索引

节点用于保存决策、实现状态、checkpoint 和实验证据。规划建立日期为 2026-09-02；初始状态不代表任何实现已经完成。

| 节点 | 页面 | 状态 | 产物类型 |
|---|---|---|---|
| T-00 | [基线与数据合同冻结](T-00/README.md) | passed | baseline/schema manifests |
| T-01 | [覆盖性轨迹采集](T-01/README.md) | passed | dataset/coverage/split manifests |
| T-02 | [Graph World Model 基线](T-02/README.md) | planned | base WM checkpoints/reports |
| T-03 | [自动事件与 GES](T-03/README.md) | blocked_by_T-02 | event/EAWM checkpoints/ablations |
| T-04 | [Shadow 与校准](T-04/README.md) | blocked_by_T-03 | shadow/calibration/safety evidence |
| T-05 | [冻结 latent 接入 GPPO](T-05/README.md) | blocked_by_T-04 | policy checkpoints/ablations |
| T-06 | [短期 imagined rollout](T-06/README.md) | blocked_by_T-05 | rollout checkpoints/held-out results |

更新节点时：复制[节点记录模板](templates/NODE_RECORD_TEMPLATE.md)的证据结构，在对应目录保存 manifest；同步更新 [`status.json`](status.json)；最后把节点页中的证据链接固定到 Git commit 或 versioned Release。

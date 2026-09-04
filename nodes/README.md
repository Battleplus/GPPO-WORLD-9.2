# 节点总索引

节点用于保存决策、实现状态、checkpoint 和实验证据。规划建立日期为 2026-09-02；下表已同步到 [`status.json`](status.json) 的当前状态。面向阅读者的完整进度说明见 [当前任务进度](../docs/05-current-progress.md)。

| 节点 | 页面 | 状态 | 产物类型 |
|---|---|---|---|
| T-00 | [基线与数据合同冻结](T-00/README.md) | passed | baseline/schema manifests |
| T-01 | [覆盖性轨迹采集](T-01/README.md) | passed | dataset/coverage/split manifests |
| T-02 | [Graph World Model 基线](T-02/README.md) | passed | base WM checkpoints/reports |
| T-03 | [自动事件与 GES](T-03/README.md) | passed | event/EAWM checkpoints/ablations |
| T-04 | [Shadow 与校准](T-04/README.md) | passed | shadow/calibration/safety evidence |
| T-05 | [冻结 latent 接入 GPPO](T-05/README.md) | passed | policy checkpoints/ablations |
| T-06 | [短期 imagined rollout](T-06/README.md) | planned / optional | rollout checkpoints/held-out results |

更新节点时：复制[节点记录模板](templates/NODE_RECORD_TEMPLATE.md)的证据结构，在对应目录保存 manifest；同步更新 [`status.json`](status.json)；最后把节点页中的证据链接固定到 Git commit 或 versioned Release。

## 基础迁移后的诊断

诊断状态单独保存在 [diagnostics-status.json](diagnostics-status.json)，不改写 T-05 原实验。

- [D-02 冻结 adapter 只读诊断](D-02/README.md)：已通过 108 对非干扰验证。
- [D-03 假设判定](D-02/evidence/final-report.md)：记录已支持与未确定的解释，不作因果提升声明。
- [D-04 后续验证协议设计](D-04/README.md)：已保存设计，未启动新训练或 T-06。

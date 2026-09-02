# T-00：基线与数据合同冻结

**状态：passed（2026-09-02）**

## 目标

冻结可复现的 GPPO 运行基线、动作合同、Transition schema、字段白名单/denylist、模态注册表和初始性能/安全预算。random legal、greedy 和现有 GPPO 必须走同一 recorder/replay 通路。

## 交付物

- `baseline_manifest.json`：源提交、依赖、硬件、seed、测试命令；
- `schema.json` 与 feature/modality registry；
- 输入白名单、truth-only denylist、版本与时间语义；
- 动作合同：候选边/NOOP、proposal/executed/ACK 的区分；
- 基线 GPPO checkpoint inventory 与可加载性报告；
- 初始延迟、安全和任务指标，用于冻结后续 Gate 数值。

## Gate

- 所有在线输入都能证明在 `decision_time` 可见；
- `executed_action` 不能被 raw proposal 替代；
- future graph/mask、未到达消息、truth-only 字段测试必须拒绝；
- 同一轨迹通过 recorder 重放得到一致样本；
- 原 GPPO forward、保存/加载和最小训练通过。

## Gate 结果

| Gate | 结果 | 证据 |
|---|---|---|
| 固定 `GPPO-8.29@2a9bb9f`、环境与源文件哈希 | PASS | [baseline manifest](evidence/baseline-manifest.json) |
| 原 GPPO 核心、最小 PPO、并发、事件桥接 | 50/50 PASS | [基线测试报告](evidence/baseline-test-report.md) |
| 16 候选边 + NOOP、三类节点、合法动作前向 | PASS | [真实适配输出](evidence/gppo-adapter-validation.json) |
| 因果输入、future/truth denylist、executed-action 合同 | 15/15 PASS | [合同测试报告](evidence/contract-test-report.md) |
| random/greedy/GPPO 统一 recorder 与确定性序列化 | PASS | [合同测试报告](evidence/contract-test-report.md) |

## 保存点

T-00 合同实现提交为 `22487f93740ddd1ef428bf0bd7c4f45f7cee27f7`，保存点见 [checkpoint manifest](evidence/checkpoint-manifest.json)。本节点不产生模型权重；历史 12 个 checkpoint 只有来源清单且无二进制，明确标记为未加载验证。

## 解锁

[T-01](../T-01/README.md) 已解锁。

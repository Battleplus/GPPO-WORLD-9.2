# T-02：Graph World Model 基线

**状态：passed（2026-09-02）**

## 目标

建立无自动事件头的动作条件异构图世界模型，先回答“模型是否真正学习 executed action 的后果”。本节点不修改 GPPO 策略。

## 模块

- typed graph encoder；
- executed-action encoder；
- temporal latent dynamics `[h_t, z_t]`；
- next graph/delta、reward、cost、continuation、uncertainty heads；
- 独立训练、评估、checkpoint 保存/加载与恢复。

## 对照

- last value / frequency；
- 等预算 summary-vector GRU；
- no-action；
- action-shuffle；
- graph world model。

## Gate

- checkpoint roundtrip 输出在冻结容差内一致；
- held-out 一步预测优于 T-00 冻结的朴素基线；
- 1/3/5-step 误差完整报告；
- 合法 action-counterfactual 相对正确 action 的 state/reward/cost 显著变差；
- no-action 结果完整报告；其显著性作为诊断项，不替代合法动作反事实硬 Gate；
- uncertainty 与误差风险呈可用的单调关系。

若合法动作反事实不影响结果，说明模型未使用动作条件，本节点不得通过。动作反事实只能从当前
`action_mask` 的合法集合中选择，并从同一历史 hidden state 分叉；置信区间按 episode bootstrap，
不得用非法动作或打乱整段历史制造退化。

## 保存点

- 实现提交：[`68d55db`](https://github.com/Battleplus/GPPO-WORLD-9.2/commit/68d55db239a9992b40f0b485d4e7fec26aa2b136)
- checkpoint 与训练资产：[T-02 Release v0.1.0](https://github.com/Battleplus/GPPO-WORLD-9.2/releases/tag/t02-base-wm-v0.1.0)
- [checkpoint manifest](evidence/checkpoint-manifest.json)
- [完整指标与 Gate](evidence/metrics.json)
- [训练配置、seed 与 validation-only 校准](evidence/training-config.json)
- [严格输入审计](evidence/input-audit.json)
- [训练日志资产清单](evidence/training-log-manifest.json)
- [测试与限制报告](evidence/test-report.md)
- [保留的失败 run](evidence/failed-run.json)

## Gate 结果

| Gate | 结果 |
|---|---:|
| 无 post-action future interval 输入 | PASS |
| T-01 hashes/groups/truth/checkpoint 重新验证 | PASS |
| 全部 8 类关系、384 维状态目标 | PASS |
| Graph-WM MAE `0.0487038303` < last-value `0.0490300734` | PASS |
| 合法反事实 state/reward/cost 的 episode-bootstrap CI 下界均大于 0 | PASS |
| 非法反事实动作数 | 0 |
| uncertainty/error Spearman `0.632530855`，高/低风险比 `4.2265` | PASS |
| Graph/Flat checkpoint roundtrip 最大绝对差 | 0 / 0 |
| Graph/Flat 参数差 `0.3028%` | PASS |
| 1/3/5-step MAE | `0.04844 / 0.11180 / 0.17614` |

等预算 Flat-GRU 的 state MAE (`0.04605`) 优于当前 Graph-WM，no-action state CI 也跨 0；两项负结果均已
保留。T-02 通过只表示基础因果 Graph-WM 的保存、恢复、预测与动作使用 Gate 成立，不表示图结构已优于
所有基线，也不表示 GPPO 下游收益成立。

## 解锁

[T-03](../T-03/README.md) 已解锁。

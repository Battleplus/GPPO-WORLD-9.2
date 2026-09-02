# T-03：自动事件、Event Head 与 GES

**状态：passed（2026-09-02）**

## 目标

将 EAWM 的事件感知思想迁移到异构图：从相邻可见观测自动生成事件，训练按模态的 Event Predictor，并用 GES 控制高密度边界对训练的影响。

## 实现

- ordinal：DOWN/SAME/UP；
- nominal：SAME/CHANGED 或类别转移；
- structural：node/edge/relation/action-support 变化；
- evidence：new/duplicate/conflict/confirm/expire；
- semantic event head：如需要，只作为独立辅助/审计头；
- hard GES 主实现，smooth GES 作为消融；
- class-balanced CE/focal 仅使用 train split 统计。

## 公平消融

1. `WM`；
2. `WM + Event (no GES)`；
3. `WM + Event + GES`。

模型容量、数据、seed、训练步数和评估脚本保持一致。Event logits 默认不直接进入 GPPO actor。

## Gate

- 自动事件生成 byte-identical；
- 阈值/range/eligible mask 来自物理合同或 train split 并已冻结；
- macro-F1/AUPRC 和稀有事件 recall 超过频率基线；
- GES 密度与权重可审计；
- 基础 next-state/reward/cost 预测不超过冻结的退化上限；
- 负结果和失败 seed 保留。

## 保存点

- 实现提交：[`1d02beb`](https://github.com/Battleplus/GPPO-WORLD-9.2/commit/1d02beb8cce6e90d2cf2d84abf69c9666ce73db3)
- checkpoint、训练历史、逐 seed 指标和失败 run：[T-03 Release v0.1.0](https://github.com/Battleplus/GPPO-WORLD-9.2/releases/tag/t03-eawm-v0.1.0)
- [三 seed 聚合指标与 Gate](evidence/aggregate-metrics.json)
- [checkpoint/release 资产清单与 SHA-256](evidence/checkpoint-manifest.json)
- [冻结训练配置](evidence/training-config.json)
- [train-only 事件 schema](evidence/event-schema.json)
- [严格输入审计](evidence/input-audit.json)
- [测试与限制报告](evidence/test-report.md)
- [保留的失败配置](evidence/failed-runs.json)

## Gate 结果

| 指标 | 三 seed 结果 |
|---|---:|
| EAWM-hard macro-F1 | `0.466769 ± 0.004970` |
| EAWM-hard macro-AUPRC | `0.431982 ± 0.013572` |
| EAWM-hard rare-event recall | `0.153531 ± 0.021994` |
| 相对 WM 的最大 state MAE 退化 | `0.3385%` |
| 相对 WM 的最大 reward MAE 退化 | `0.4692%` |
| 相对 WM 的最大 cost MAE 退化 | `1.2144%` |
| 自动标签重复生成 | byte-identical |
| checkpoint roundtrip | 最大绝对差 `0` |

三组主消融在每个 seed 上使用同一初始化、参数量、数据、episode 顺序规则与 20 epoch 固定预算。
smooth GES 只作为 seed `20260903` 的敏感性实验。T-01 没有 TTL/expiry 合同，因此 `expire` 目标被明确
标为 ineligible，不能被包装成全负类成功。发布资产保留了两次预冻结失败：`event_weight=0.50` 的
seed `20260905` 和未缩放主干学习率的 seed `20260904`。

协议披露：初次测试结果在冻结主干学习率倍率前已被查看；最终修正同时由 validation 侧的 reward 退化支持，
但最终三 seed 结果不宣称为“首次盲测”。完整披露位于聚合指标和测试报告中。

## 解锁

[T-04](../T-04/README.md) 已解锁。

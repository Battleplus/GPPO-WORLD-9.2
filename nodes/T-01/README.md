# T-01：覆盖性轨迹采集

**状态：passed（2026-09-02）**

## 目标

用同一 recorder 采集 random legal、greedy、现有 GPPO 三类行为策略轨迹，使世界模型同时看到常见动作和策略较少访问的合法状态。

## 覆盖范围

- normal、single event、sequential、overlap、burst；
- weak communication、long observation gap；
- 不同 scenario、event tape、seed；
- 合法候选边、NOOP、执行失败/拒绝、stale 与恢复路径。

## 交付物

- episode 级数据集和 `dataset_manifest.json`；
- action/state/event coverage report；
- train/validation/test 的 episode/scenario/seed 清单与 SHA-256；
- 自动事件分布、稀有类别支持数、missing/validity 统计；
- 抽样 replay 对齐和无泄漏审计。

## Gate

- split 分组交叉数为 0；
- truth-only 在线字段数为 0；
- executed action 可追踪到版本与执行结果；
- 三类行为策略和规定压力场景均达到 T-00 冻结的最小覆盖；
- manifest 能从原始轨迹重建同一 split。

## Gate 结果

| Gate | 结果 | 证据 |
|---|---|---|
| random legal / greedy / GPPO 统一 recorder | 3/3 覆盖 | [dataset manifest](evidence/dataset-manifest.json) |
| normal/single/sequential/overlap/burst/long gap/weak comm | 7/7 覆盖 | [audit report](evidence/audit-report.json) |
| episode/scenario/tape/seed 严格切分 | 42 groups，交叉 0 | [audit report](evidence/audit-report.json) |
| 因果字段审计 | truth-only 在线字段 0 | [audit report](evidence/audit-report.json) |
| 动作覆盖 | action 0～16 全覆盖 | [audit report](evidence/audit-report.json) |
| 事件覆盖 | 四类事件共 144 次 | [audit report](evidence/audit-report.json) |
| GPPO coverage checkpoint | roundtrip 与合法前向 PASS | [checkpoint manifest](evidence/checkpoint-manifest.json) |

## 数据与 checkpoint

- [T-01 GitHub Release](https://github.com/Battleplus/GPPO-WORLD-9.2/releases/tag/t01-data-v0.1.0)
- 126 episodes、502 transitions；train/validation/test 分别为 173/166/163。
- checkpoint 为 Python 3.11、seed 1101 下本地训练的 512-step `GPPO-Adaptive`，只服务于行为覆盖；不是缺失的历史 50k checkpoint。
- 三份 JSONL、训练 history 和 checkpoint 均在 Release 中，SHA-256 固定在 manifest。

## 回退

发现泄漏或 split 污染时，受影响数据及其派生 checkpoint 全部标记 rejected，修复 exporter 后重新生成。

## 解锁

[T-02](../T-02/README.md) 已解锁。

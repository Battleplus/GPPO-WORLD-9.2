# T-01：覆盖性轨迹采集

**状态：blocked by T-00**

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

## 回退

发现泄漏或 split 污染时，受影响数据及其派生 checkpoint 全部标记 rejected，修复 exporter 后重新生成。

## 解锁

通过后解锁 [T-02](../T-02/README.md)。

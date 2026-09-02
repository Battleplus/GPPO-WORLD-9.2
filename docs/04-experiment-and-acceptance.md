# 实验矩阵与验收定义

## 1. 公平消融矩阵

| 组别 | 历史世界模型 | 自动事件头 | GES | latent 接入 GPPO | imagined rollout |
|---|---:|---:|---:|---:|---:|
| GPPO | 否 | 否 | 否 | 否 | 否 |
| GPPO-History | 仅等预算历史编码 | 否 | 否 | 历史上下文 | 否 |
| WM-GPPO | 是 | 否 | 否 | 是 | 否 |
| EA-noGES-GPPO | 是 | 是 | 否 | 是 | 否 |
| EAWM-GPPO | 是 | 是 | 是 | 是 | 否 |
| EAWM-Imagine-GPPO | 是 | 是 | 是 | 是 | 1～3 步 |

所有组固定：环境与场景、事件带、可见性、动作空间与 mask、奖励/成本、GPPO 超参数、训练步数、seed、硬件预算、评估脚本。参数量或延迟不等时必须报告，不能默认为公平。

## 2. 指标

### 世界模型

- node/edge/state delta：MAE、RMSE、structural F1；
- reward/cost：MAE、rank correlation、约束违例召回；
- continuation：AUROC、AUPRC、Brier；
- 多步：1/3/5-step error 与误差累积曲线；
- 动作敏感性：action-shuffle、no-action、counterfactual candidate 对照。

### 自动事件

- macro-F1、macro-AUPRC；
- 每模态、每事件 recall/FPR；
- 稀有事件支持数；
- GES 开/关时基础预测与事件预测的共同变化。

### 不确定度与部署

- ECE、Brier、NLL、risk-coverage；
- ID/OOD、弱通信、长间隔、burst 场景；
- P50/P95/P99 延迟、峰值内存、异常率、回退率；
- belief/mask/version 写入次数、非法动作、stale 提交。

### GPPO 业务结果

- 任务完成率、makespan、累计 reward/cost；
- uncovered duration、distance、load balance、switch/recovery；
- 通信次数、bytes、stale/duplicate；
- unseen seed、unseen event combination、长 gap 与 burst 泛化。

## 3. 节点硬 Gate

阈值由 T-00 基线测量和业务预算冻结；当前设计不捏造数值。下列关系型条件不可删除：

- T-01：episode/scenario/seed split 交叉数为 0；truth-only 在线字段数为 0。
- T-02：action shuffle 后下一状态/reward/cost 预测显著变差；模型独立保存加载一致。
- T-03：事件指标超过频率/多数类基线；加入事件后基础预测不出现预先定义的不可接受退化。
- T-04：shadow 对 belief、mask、version 的写入次数为 0；异常/超时/OOD 全部进入安全回退。
- T-05：非法动作和 stale 漏拦截不高于原 GPPO；关闭 WM 后恢复原路径；旧 checkpoint 可加载。
- T-06：真实 held-out 环境取得独立、重复 seed 可见的收益；1/3/5-step 误差透明报告。

统计报告至少包含均值、离散度、置信区间或 bootstrap 区间、逐 seed 结果和失败 run，不只展示最佳 seed。

## 4. “世界模型迁移完成”定义

必须全部满足：

1. 动作条件异构图世界模型和严格数据切分已实现；
2. state/event/reward-cost/continuation/calibration 有独立评估；
3. GPPO 可选读取冻结 latent，关闭后无损回退；
4. 世界模型不污染 belief、mask、版本或并发安全链；
5. 至少完成 GPPO、WM-GPPO、EA-noGES-GPPO、EAWM-GPPO 四组公平对照；
6. 每项结论能追溯到 checkpoint、配置、seed、日志、结果和代码 commit。

T-06 imagined rollout 不是基础迁移完成的必要条件；它是基础迁移通过后的扩展能力。

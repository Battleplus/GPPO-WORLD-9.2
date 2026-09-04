# T-05 封存后的诊断与下一步

日期：2026-09-04。状态：D-01 已执行；后续训练和 T-06 尚未开始。

## 已完成的下一步：只读诊断

在 [T-05 Release](https://github.com/Battleplus/GPPO-WORLD-9.2/releases/tag/t05-gppo-ablation-v0.1.0) 全量下载校验完成后，用 [诊断脚本](../tools/diagnose_t05_frozen_results.py) 读取 12 个评估和 1,200 条 trace。脚本验证固定归档 SHA-256、group/seed/tape 配对、每场景 20 条轨迹、逐决策 reward 分项守恒与两类累计 return。

输出：[机器可读事后诊断](../nodes/T-05/evidence/posthoc-diagnostics.json)。本次不加载模型、不执行归档代码、不修改 checkpoint，不重新训练或选择模型；全部是描述性事后分析，不是新的确认性实验。

## 发现一：先区分奖励口径

固定基线 `ppo_allocation/random_event/experiment.py` 的 `run_episode` 把每次 reward 仅归给第一个 `active_before` 事件，避免多个事件重复计分；如果当时没有活跃事件，该 reward 不进入 event accumulator。`metrics.py` 的 `aggregate_episode` 将这些 event returns 相加，形成原有 `episode_return`。

所以有两种不同的量：

- 正式 `episode_return`：归属于活跃事件的累计奖励，本次封存指标保持不变；
- `all_decision_return`：所有已接受决策的奖励总和，对应 trace 中的 `episode_return_check`。

两者不相等不代表文件损坏，也不能在看过结果后替换正式主指标。此次补充分析将两种口径并列，下一轮实验应事先声明用途。

| Seed | EAWM − GPPO：正式事件归因 return | EAWM − GPPO：全部决策 return |
|---:|---:|---:|
| 1101 | -1.809860 | -0.092405 |
| 2202 | -0.928935 | -0.131458 |
| 3303 | +0.014764 | +0.165249 |

这里的全部决策 return 仅是描述性均值，未做新的置信区间或确认性检验，不能据此宣布性能提升。正式事件归因 return 的原 bootstrap 结果继续有效。

## 发现二：下降不集中于同一个场景

下表为 EAWM − GPPO 的正式事件归因 return；每格是同 seed、同场景的 20 条 tape 配对差值均值。

| 场景 | Seed 1101 | Seed 2202 | Seed 3303 |
|---|---:|---:|---:|
| single | -2.4301 | -1.1008 | -0.5348 |
| sequential | -1.9330 | -2.3802 | +1.2060 |
| overlap | -1.1105 | -1.4786 | +0.0060 |
| burst | -2.2699 | +0.5383 | -0.4825 |
| unseen | -1.3059 | -0.2234 | -0.1208 |

这是定位线索，不是按场景筛选最佳模型的依据。当前仍不支持稳定的一般性 GPPO 增益。

## 发现三：分项和实际 latent 使用情况

按基线事件归因规则重算 reward components 后，EAWM − GPPO 的均值差如下；同一行分项之和等于正式 return 差值。

| Seed | uncovered 分项 | distance 分项 | load gap 分项 | switches 分项 | recovery 分项 |
|---:|---:|---:|---:|---:|---:|
| 1101 | -1.45335 | +0.01599 | -0.11000 | +0.07250 | -0.33500 |
| 2202 | -0.75170 | +0.01527 | -0.06000 | +0.03750 | -0.17000 |
| 3303 | +0.10035 | -0.00559 | -0.11000 | -0.00500 | +0.03500 |

前两个 seeds 的差距主要体现在 uncovered reward 分项。这不等于“累计未覆盖时间一定变差”，因为奖励分项衡量决策前后成本差，而业务累计时间是另一种量；也不证明 GES 是原因。

EAWM 三个 seeds 的 adapter 实际使用次数为 `487/635`、`488/634`、`488/635`，约 77%。未使用包括每 episode 初始化与有效性回退等路径，不应把其余约 23% 全部算成模型故障。原始计数保存在诊断 JSON 中。

## 后续推进计划

| 步骤 | 范围与产物 | 状态/通过条件 |
|---|---|---|
| D-01 | 冻结 Release 的奖励口径、场景和分项诊断 | 已完成；1,200 条 trace 双口径守恒验证，52 项测试通过 |
| D-02 | 在非 Test 的开发数据上记录 adapter residual 大小、baseline/adapter 动作分歧、first-step/invalid/stale/OOD 回退原因 | 待实施；只增加只读诊断，不改动作、mask 或奖励 |
| D-03 | 将“事件归因与全决策 return 的差异”“latent 分布与适配器优化问题”作为待验证假设 | 先用 Train/Validation 检查，不把 D-01 当因果证明；不得调优已看过的 Test |
| D-04 | 单独冻结新一轮协议：主指标及方向、配对 seeds、预算、未查看的新 Test bank、无 WM/zero-context/历史对照 | 待计划确认；配置和数据 hash 冻结后再启动新训练 |
| T-06 | 可选 horizon=1，再到 3 的 imagined rollout | 尚未开始；另立验收，不自动纳入当前基础迁移 |

优先顺序是先解释和验证 T-05 的收益缺口，再评估是否需要 T-06。世界模型继续只提供预测/context，GPPO 和真实执行安全链保持最终动作权威。

## 复现

下载 Release 的 `t05-evaluation-artifacts.tar.gz` 后，在仓库根目录执行：

```text
python tools/diagnose_t05_frozen_results.py /path/to/t05-evaluation-artifacts.tar.gz /new/path/posthoc-diagnostics.json
python -m pytest -q
```

输出路径必须尚不存在，避免覆盖已封存诊断；脚本拒绝非本次 Release 的归档哈希。

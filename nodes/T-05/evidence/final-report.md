# T-05 正式四组消融最终报告

更新时间：2026-09-04（Asia/Shanghai）

## 结论

T-05 的接口、兼容、安全和正式实验 Gate 均已通过：冻结世界模型 latent 已通过可关闭 adapter 接入 GPPO，原 GPPO 仍是唯一动作选择器；四组 × 三 seeds 的 12 个正式 run 和固定 50k checkpoint 的 12 次 held-out 评估全部完成。

实验**不支持“世界模型稳定提升 GPPO”这一普遍性能结论**。这是被完整保留的负结果，不影响“世界模型基础迁移完成”的工程验收。T-06 imagined rollout 和人类偏好奖励不在本次范围内。

## 冻结协议与完整性

- GPPO 基线：`2a9bb9f87b9d543df144f4d108ba970c924151f9`；
- 正式运行代码：`69e3be5931deea7371df77d75fb14f2f5bdeab72`；
- 配置 SHA-256：`973dc586fb0bac268ab753c180b8a19cfe0e01430b3bd9251c91118af4871225`；
- Test manifest SHA-256：`f295bc42ba932ed192162f231670de3865dedae7f2d737331576b90f2cf88bf5`；
- 聚合结果 SHA-256：`0f64696b6706e1cb711d5ab0987361172c2cdad3b0fe7ef78d6906ec8303f794`；
- 四组：GPPO、WM-GPPO、EA-noGES-GPPO、EAWM-GPPO；
- seeds：1101、2202、3303；每 run 为 50,000 accepted decision steps；
- 25k/50k checkpoint 共 24 个，全部通过 SHA-256 校验；
- 固定 50k checkpoint 在同一有序 100-tape Test bank 上评估；12 个评估、1,200 条 trace 全部通过清单与内容哈希复核；
- 未使用 Test 结果选择 checkpoint，聚合状态为 `evaluated_no_checkpoint_selection`。

完整大文件封存于 [T-05 Release v0.1.0](https://github.com/Battleplus/GPPO-WORLD-9.2/releases/tag/t05-gppo-ablation-v0.1.0)。仓库内保存运行、评估、测试带、顶层文件和 Release 资产清单。

## 四组 held-out 均值

口径说明：以下 `episode_return` 沿用固定基线的活跃事件归因累计奖励，不等于全部决策奖励总和。两种量的事后对照见 [后续诊断](../../../docs/08-post-t05-diagnostics-and-next-plan.md)，不得以补充口径替换本次正式指标。

| 组 | Episode return ↑ | Fixed J ↓ | Event success ↑ | Final infeasible ↓ | Uncovered time ↓ | Recovery delay ↓ | Inference latency ms ↓ |
|---|---:|---:|---:|---:|---:|---:|---:|
| GPPO | 25.617799 | 96.005833 | 0.954000 | 0.046000 | 8.623073 | 1.705619 | 3.753611 |
| WM-GPPO | 25.138844 | 95.980514 | 0.954667 | 0.045333 | 8.643420 | 1.687605 | 4.151101 |
| EA-noGES-GPPO | 25.666769 | 96.350701 | 0.953333 | 0.046667 | 8.653553 | 1.708943 | 4.224379 |
| EAWM-GPPO | 24.709788 | 96.361733 | 0.954667 | 0.045333 | 8.597057 | 1.671878 | 4.143277 |

EAWM-GPPO 的 recovery delay 均值略低，但 `fixed_j` 是越低越好的成本，均值从 GPPO 的 96.005833 上升到 96.361733，并非改善。指标方向以固定基线的 `ppo_allocation/random_event/phase_j.py` 中 `lowest_fixed_j` 和成本定义为准。episode return 的逐 seed 配对结果如下：

| Seed | EAWM − GPPO episode return | 95% paired bootstrap CI |
|---:|---:|---:|
| 1101 | -1.809860 | [-2.554067, -1.075247] |
| 2202 | -0.928935 | [-1.594782, -0.356410] |
| 3303 | +0.014764 | [-0.624246, +0.667431] |

因此不能宣称 EAWM 对 GPPO 有稳定的一般性增益。后续若研究收益，应以独立的新 Test bank、更多 seeds 或 T-06 的单独新协议验证，不能回头挑选本次 checkpoint。

## 安全、回退与运行门禁

- 12/12 run 的环境、belief、action mask 和 graph/action version 突变计数均为 0；
- 9 个世界模型组 run 的 Shadow belief/mask/version 写入与动作提交均为 0；GPPO 组未实例化世界模型 runtime；
- 世界模型保持冻结，`world_trainable=0`，不进入 PPO optimizer；
- 所有 Shadow P95/P99 延迟门禁通过，timeout 为 0；
- disabled、zero、invalid、stale 和旧 checkpoint 路径保持原 GPPO 回退合同；
- 一次 GPPO seed 1101 的初始尝试在任何 accepted decision 前因 CRLF/LF 校准哈希不匹配失败，失败日志被保留；修复后的正式结果位于 `seed1101-attempt-2`，未覆盖失败记录。

## 证据入口

- [聚合结果](four-group-ablation.json)
- [正式运行清单](server-run-manifest.json)
- [正式评估清单](server-evaluation-manifest.json)
- [最终摘要](server-final-summary.json)
- [失败运行记录](server-failed-runs.json)
- [Test bank 清单](server-test-bank-manifest.json)
- [顶层文件清单](server-top-level-inventory.json)
- [Release 资产 SHA-256](release-assets-sha256.txt)
- [服务器环境预检](server-environment-preflight.txt)
- [独立证据与 Release 资产复核](independent-release-audit.md)

`server-final-summary.json` 是发布前生成的不可变服务器快照，因此其中 `release_status=prepared_not_published` 描述的是快照时刻；实际发布状态以本报告的 Release 链接和 GitHub Release 页面为准。

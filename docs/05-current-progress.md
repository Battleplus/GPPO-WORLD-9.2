# GPPO 世界模型迁移当前进度

> **服务器实时状态补充：** 正式 T-05 campaign 已于 2026-09-03 启动。当前运行身份、双 GPU worker 和接力说明见 [`07-t05-live-server-campaign-handoff.md`](07-t05-live-server-campaign-handoff.md)。本文件其余统计仍是启动前基线，最终状态须等待 12/12 训练、12/12 评估和聚合完成后统一更新。

更新时间：2026-09-03（Asia/Shanghai）

## 一页结论

GPPO 世界模型基础迁移已经完成 T-00～T-04，并完成 T-05 的代码接入、本地接口验证、安全零写入验证、旧 GPPO 无损回退和服务器实验协议。正式 T-05 四组多 seed GPU 消融尚未运行，因此当前不能宣称迁移完成，也不能宣称世界模型已经改善 GPPO。

当前权威状态：

- T-00～T-04：`passed`；
- T-05：`in_progress`，本地 Gates 已通过，正式服务器实验 `0/12`；
- T-06：不属于本目标，且被 T-05 阻塞；
- 唯一外部阻塞：没有可达、可认证并能返回 CUDA 信息的服务器。

## 版本锚点

| 项目 | 固定版本 |
|---|---|
| GPPO 设计与数据基线 | [`Battleplus/GPPO-8.29@2a9bb9f`](https://github.com/Battleplus/GPPO-8.29/commit/2a9bb9f87b9d543df144f4d108ba970c924151f9) |
| T-05 代码目标提交 | [`a4432a9`](https://github.com/Battleplus/GPPO-WORLD-9.2/commit/a4432a9527c73021d605f6960dfcc5b8d3e3b3c6) |
| 本进度整理前的仓库 HEAD | [`3142425`](https://github.com/Battleplus/GPPO-WORLD-9.2/commit/31424251d7801523558502a39501f12aded20674) |
| T-05 服务器配置 SHA-256 | `8373cb3b8a40d6313a8a58c2560ad9985af82ea23fa0049308382862de73351c` |

机器可读的当前状态以 [`nodes/status.json`](../nodes/status.json) 为准。

## 节点进度与证据

| 节点 | 状态 | 已完成内容 | 关键证据 |
|---|---|---|---|
| T-00 | **passed** | 冻结因果 Transition 合同、在线字段白名单、future/truth denylist、proposal/executed action 与版本语义；删除在线 future `delta_time` 泄漏 | [节点说明](../nodes/T-00/README.md)、[基线清单](../nodes/T-00/evidence/baseline-manifest.json)、[合同测试](../nodes/T-00/evidence/contract-test-report.md)、[因果修正](../nodes/T-00/evidence/causal-correction-report.md) |
| T-01 | **passed** | 建立 126 episodes / 502 transitions 数据集；三类行为策略、七类场景、17 动作全覆盖；完整 group split overlap=0，在线 truth-only 字段=0 | [节点说明](../nodes/T-01/README.md)、[数据审计](../nodes/T-01/evidence/audit-report.json)、[checkpoint 清单](../nodes/T-01/evidence/checkpoint-manifest.json)、[Release](https://github.com/Battleplus/GPPO-WORLD-9.2/releases/tag/t01-data-v0.1.0) |
| T-02 | **passed** | 实现动作条件异构图世界模型、时序 dynamics、next-state/reward/cost/continuation/uncertainty heads；合法动作反事实证明模型实际使用动作 | [节点说明](../nodes/T-02/README.md)、[指标](../nodes/T-02/evidence/metrics.json)、[checkpoint 清单](../nodes/T-02/evidence/checkpoint-manifest.json)、[Release](https://github.com/Battleplus/GPPO-WORLD-9.2/releases/tag/t02-base-wm-v0.1.0) |
| T-03 | **passed** | 实现自动事件、Event Predictor、hard/smooth GES；完成 WM、EA-noGES、EAWM 三 seed 固定预算消融并保存负结果 | [节点说明](../nodes/T-03/README.md)、[聚合指标](../nodes/T-03/evidence/aggregate-metrics.json)、[checkpoint 清单](../nodes/T-03/evidence/checkpoint-manifest.json)、[Release](https://github.com/Battleplus/GPPO-WORLD-9.2/releases/tag/t03-eawm-v0.1.0) |
| T-04 | **passed** | 实现只读 post-action Shadow、校准、OOD/risk-coverage、延迟与安全回退；真实 belief/action mask/version/动作提交写入均为 0 | [节点说明](../nodes/T-04/README.md)、[指标](../nodes/T-04/evidence/metrics.json)、[Shadow bundle](../nodes/T-04/evidence/accepted-shadow-bundle.json)、[Release](https://github.com/Battleplus/GPPO-WORLD-9.2/releases/tag/t04-shadow-v0.1.0) |
| T-05 | **in progress** | 冻结 latent adapter、逐 transition versioned sidecar、旧 checkpoint 兼容和服务器训练/评估/聚合入口已完成；21 个本地 Gates 与 44 项测试通过 | [节点说明](../nodes/T-05/README.md)、[本地接口验证](../nodes/T-05/evidence/local-interface-validation.json)、[本地测试](../nodes/T-05/evidence/local-test-report.md)、[服务器探测](../nodes/T-05/evidence/server-probe.json) |

## T-05 已经完成的部分

- 冻结 `[h,z]` residual adapter 同时接入 actor 与 critic，动作空间保持 16 条 UAV–Region 候选边加 NOOP；
- disabled、invalid、stale 和 zero-context 路径恢复原 GPPO；旧 checkpoint 加载后保持 bit-exact logits/value；
- Shadow 只在实际动作确认后读取 `graph_t + confirmed executed action + decision_time 前证据`；执行拒绝和 stale 决策不进入 Shadow；
- rollout buffer 为每个 transition 保存不可变 latent、graph version 和 action version，shuffle/update 仍使用同一上下文；
- 世界模型保持 `eval`、完全冻结并排除在 PPO optimizer 外；在线 context 不跨 episode/checkpoint 恢复；
- 真实基线 12-transition smoke 观察到 12 次有效 Shadow 与 23 条 decision-time evidence；
- 环境、belief、action mask、graph/action version 和动作提交接口的写入/突变计数均为 0；
- 服务器 runner、固定 50k checkpoint evaluator、12-run aggregator、冻结配置和运行手册已经提交。

本地验证不是性能实验，也不是 T-05 通过证明。详细门禁见 [`local-interface-validation.json`](../nodes/T-05/evidence/local-interface-validation.json)。

## T-05 尚未完成的部分

必须在 CUDA 服务器完成以下固定实验：

| 实验组 | seeds | 每个 run 预算 | 当前完成 |
|---|---|---:|---:|
| GPPO | 1101、2202、3303 | 50,000 accepted decisions | 0/3 |
| WM-GPPO | 1101、2202、3303 | 50,000 accepted decisions | 0/3 |
| EA-noGES-GPPO | 1101、2202、3303 | 50,000 accepted decisions | 0/3 |
| EAWM-GPPO | 1101、2202、3303 | 50,000 accepted decisions | 0/3 |
| **合计** | 3 seeds × 4 groups | **600,000 accepted decisions** | **0/12** |

所有 run 还必须产生 25k/50k checkpoints、环境清单、history/progress、safety audit 和 SHA-256 inventory；固定 50k checkpoint 必须在同一 100 条 held-out Test tapes 上评估，最后输出逐 seed、配对效应、离散度与 bootstrap 区间。Test 结果不得用于挑选 checkpoint。

执行协议见 [`nodes/T-05/SERVER_RUNBOOK.md`](../nodes/T-05/SERVER_RUNBOOK.md)，冻结配置见 [`server-training-config.json`](../nodes/T-05/server-training-config.json)。如果由另一名 AI/工程师连接服务器接力执行，应从 [T-05 服务器训练 AI 接力说明](06-server-ai-handoff.md) 开始，其中包含隔离 checkout、环境准备、12-run 矩阵、评估、聚合、Release 与 PR 的完整步骤。

## 当前阻塞与恢复条件

最近的只读探测覆盖 9 个已配置 SSH 目标：可认证 CUDA 主机为 0，正式 runs 为 0，且没有修改任何远端状态。证据见 [`server-probe.json`](../nodes/T-05/evidence/server-probe.json)。

恢复工作只需要满足以下条件：

1. 连接服务器所在 VPN，或配置一台可以通过现有 SSH key 登录的 CUDA 服务器；
2. 提供该服务器的 SSH `Host alias`，无需在聊天或仓库中保存密码；
3. 在服务器按冻结 runbook 执行 12 runs、12 次固定 checkpoint 评估和一次聚合；
4. 将 checkpoints/logs/metrics/inventory 上传到不可变 GitHub Release，并把紧凑证据提交到 T-05；
5. 只有所有安全计数仍为 0、旧 GPPO 回退仍 bit-exact 且聚合完整，才能把 T-05 改为 `passed`。

## 当前不能作出的声明

- 不能声称世界模型已经提高 GPPO 的 held-out return、成本、安全性或样本效率；
- 不能把本地 12-transition smoke 当成正式训练结果；
- 不能把 T-03 世界模型内部指标当成 T-05 下游策略增益；
- 不能标记“基础迁移完成”；
- 不启动 T-06 imagined rollout，也不引入人类偏好奖励。

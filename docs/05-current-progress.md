# GPPO 世界模型迁移当前进度

更新时间：2026-09-05（Asia/Shanghai）

## 一页结论

2026-09-05 复审完成：[重新分析](09-project-reassessment-20260905.md) 与 [修订规划](10-revised-experiment-plan-20260905.md) 已保存，186 个封存文件身份核验通过。**用户原始目标要求的 GPPO-History 对照缺失，完整验收尚未全部满足**；T 节点的历史 `passed` 仅指其已执行协议。原始要求覆盖以 [requirements-status.json](../nodes/requirements-status.json) 为准。下一步先做开发机制诊断和 pre/commit/next 时间目标合同，尚未启动新训练。

新增进展：独立 [J-01 Graph-JEPA](../nodes/J-01/evidence/final-report.md) 已完成 9 次训练与 3 个随机对照，72 项测试通过；动作敏感性成立，但未来预测未超过持久化基线，统一探针明显落后于监督图对照。状态为 `experiment_completed_gate_failed`，不启动 JEPA-GPPO 训练。新图数据、模型、探针和结果已按独立 Release 封存；[J-02](../nodes/J-02/README.md) 仅是下一版设计草案。以下 T 节点结论仍指原 EAWM 路线，不可混称为 JEPA。

T-00～T-05 已按各自已执行协议通过，世界模型工程接入完成。动作条件异构图世界模型、自动事件与 GES、只读 Shadow、冻结 latent GPPO adapter、旧 GPPO 无损回退以及正式四组多 seed 消融均有可追踪证据；原始完整目标还需补历史对照。

这里的“迁移完成”是工程与实验协议结论，不等于“世界模型提升了 GPPO”。正式结果不支持稳定的一般性性能增益：EAWM-GPPO 的部分安全/恢复均值略好，但 episode return 在三个 seeds 上分别显著下降、显著下降和无显著差异。因此现阶段推荐保留可关闭 adapter 和原 GPPO 回退，不默认宣称或启用性能提升。

当前权威状态：

- T-00～T-05：`passed`；
- T-06：`planned / optional`，尚未开始且不属于本目标；
- T-06 imagined rollout 和人类偏好奖励未实现。

机器可读状态以 [`nodes/status.json`](../nodes/status.json) 为准。

## 版本与证据锚点

| 项目 | 固定版本或证据 |
|---|---|
| GPPO 设计与数据基线 | [`Battleplus/GPPO-8.29@2a9bb9f`](https://github.com/Battleplus/GPPO-8.29/commit/2a9bb9f87b9d543df144f4d108ba970c924151f9) |
| T-05 正式运行代码 | `69e3be5931deea7371df77d75fb14f2f5bdeab72` |
| T-05 服务器配置 SHA-256 | `973dc586fb0bac268ab753c180b8a19cfe0e01430b3bd9251c91118af4871225` |
| Test manifest SHA-256 | `f295bc42ba932ed192162f231670de3865dedae7f2d737331576b90f2cf88bf5` |
| 四组聚合 SHA-256 | `0f64696b6706e1cb711d5ab0987361172c2cdad3b0fe7ef78d6906ec8303f794` |
| 正式结果报告 | [T-05 最终报告](../nodes/T-05/evidence/final-report.md) |
| 大文件与 checkpoint 封存 | [T-05 Release v0.1.0](https://github.com/Battleplus/GPPO-WORLD-9.2/releases/tag/t05-gppo-ablation-v0.1.0) |

## 节点进度

| 节点 | 状态 | 已完成内容 | 关键证据 |
|---|---|---|---|
| T-00 | **passed** | 冻结因果 Transition 合同、在线字段白名单、future/truth denylist、动作和版本语义 | [节点说明](../nodes/T-00/README.md)、[因果修正](../nodes/T-00/evidence/causal-correction-report.md) |
| T-01 | **passed** | 126 episodes / 502 transitions；三类行为策略、七类场景、17 动作覆盖；group split overlap=0 | [节点说明](../nodes/T-01/README.md)、[Release](https://github.com/Battleplus/GPPO-WORLD-9.2/releases/tag/t01-data-v0.1.0) |
| T-02 | **passed** | 动作条件异构图世界模型、时序 dynamics、预测 heads 和合法动作反事实 | [节点说明](../nodes/T-02/README.md)、[Release](https://github.com/Battleplus/GPPO-WORLD-9.2/releases/tag/t02-base-wm-v0.1.0) |
| T-03 | **passed** | 自动事件、Event Predictor、hard/smooth GES，三 seed WM 消融和负结果 | [节点说明](../nodes/T-03/README.md)、[Release](https://github.com/Battleplus/GPPO-WORLD-9.2/releases/tag/t03-eawm-v0.1.0) |
| T-04 | **passed** | 只读 post-action Shadow、校准、OOD、延迟与安全回退；真实系统零写入 | [节点说明](../nodes/T-04/README.md)、[Release](https://github.com/Battleplus/GPPO-WORLD-9.2/releases/tag/t04-shadow-v0.1.0) |
| T-05 | **passed** | 冻结 latent adapter、versioned sidecar、旧 checkpoint 回退、四组 × 三 seeds × 50k 正式训练和同一 Test bank 评估 | [节点说明](../nodes/T-05/README.md)、[最终报告](../nodes/T-05/evidence/final-report.md)、[Release](https://github.com/Battleplus/GPPO-WORLD-9.2/releases/tag/t05-gppo-ablation-v0.1.0) |

## T-05 正式验收

- 训练：12/12，每 run 50,000 accepted decision steps，共 600,000；
- checkpoint：25k/50k 各 12 个，共 24 个；
- 评估：12/12，固定 50k checkpoint；
- Test：所有评估共享同一有序 100-tape bank，共 1,200 条 trace；
- 完整性：run、checkpoint、评估、trace、配置和 Test manifest 的 SHA-256 均通过独立复核；
- 公平性：四组除 group/seed 外保持冻结 PPO 协议，Test 不参与 checkpoint 选择；
- 安全性：环境、belief、action mask、graph/action version 与 Shadow action submission 写入/突变均为 0；
- 运行性：世界模型冻结，所有 Shadow 延迟 Gate 通过，timeout 为 0；
- 可追责性：一次发生在 accepted decision 前的换行符哈希失败被保留，修复重跑没有覆盖失败记录。

## 性能结论

四组 episode return 均值为：GPPO `25.617799`、WM-GPPO `25.138844`、EA-noGES-GPPO `25.666769`、EAWM-GPPO `24.709788`。

EAWM-GPPO 相对 GPPO 的逐 seed episode-return 配对差值与 95% bootstrap CI：

- seed 1101：`-1.809860`，`[-2.554067, -1.075247]`；
- seed 2202：`-0.928935`，`[-1.594782, -0.356410]`；
- seed 3303：`+0.014764`，`[-0.624246, +0.667431]`。

所以本阶段能声明：世界模型思想已安全、可关闭地迁移进 GPPO，并完成公平验证；不能声明它已经稳定改善 GPPO。世界模型不取代 GPPO，动作仍由 GPPO 在真实 mask 下自主选择。

## 下一步

已完成一轮基于封存 Release 的只读诊断，核对了 1,200 条 trace 的奖励分项、事件归因/全部决策两种 return 口径和逐场景差异。结果与后续 D-02～D-04 计划见 [T-05 封存后的诊断与下一步](08-post-t05-diagnostics-and-next-plan.md)。没有更换正式指标或重训模型。

D-02 也已在新开发集完成：108 对探针开/关复放，216 episodes、623 条决策记录全部通过非干扰与安全检查。EAWM 的 170 次 latent 使用中有 17 次改变同一 checkpoint 内 base 分支的首选动作，但这不是相对独立 GPPO 的收益证明。详见 [D-02 报告](../nodes/D-02/evidence/final-report.md) 和 [D-04 新验证设计](../nodes/D-04/README.md)。

T-06 现已从阻塞转为可选计划。若推进，必须建立新的冻结协议和独立 Test bank，再研究 1～3 步 imagined rollout；不能用本次 Test 结果反向调参或挑 checkpoint。T-06 的失败不应回滚已经通过的 T-00～T-05 基础迁移。

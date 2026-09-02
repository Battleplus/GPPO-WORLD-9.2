# T-04：Shadow、校准与风险门禁

**状态：passed（2026-09-02）**

## 目标

在线读取可信 belief/history 并更新世界模型 latent，但不影响动作选择或系统状态；测量校准、OOD、弱通信与延迟，冻结进入策略前的风险门禁。

## Shadow 日志

- 输入 graph/action/version 和 model version；
- 预测、truth、confidence/uncertainty；
- P50/P95/P99 延迟与超时；
- ID/OOD、weak communication、long gap、burst 标签；
- invalid、异常、fallback 和 stale hidden-state 丢弃；
- belief/mask/version 写入审计。

## Gate

- belief、action mask、graph/action version 写入次数均为 0；
- stale 推理不提交 latent 或 transition；
- 异常、超时、版本不一致、OOD 高风险进入 no-WM 回退；
- ECE/Brier/risk-coverage 满足 T-00 冻结阈值；
- P95/P99 时延满足预算；
- ID/OOD/弱通信测试报告齐全。

## 回退

任何 Gate 失败都保持 shadow，不得接入 actor。accepted checkpoint 需绑定 calibration 配置和 uncertainty gate，不能只保存模型权重。

## 保存点

- Shadow 实现提交：[`8880f85`](https://github.com/Battleplus/GPPO-WORLD-9.2/commit/8880f85ba3f2861988e5eafdbb6172c9d854c4e6)
- post-action 两阶段版本合同与真实基线审计提交：[`65d7a16`](https://github.com/Battleplus/GPPO-WORLD-9.2/commit/65d7a16240484797b7596c32811762f2cdfff7e9)
- 校准、完整 Shadow 记录和安全审计：[T-04 Release v0.1.0](https://github.com/Battleplus/GPPO-WORLD-9.2/releases/tag/t04-shadow-v0.1.0)
- [指标与 Gate](evidence/metrics.json)
- [accepted Shadow bundle](evidence/accepted-shadow-bundle.json)
- [校准配置](evidence/calibration.json)
- [真实 GPPO 基线零写入审计](evidence/baseline-read-only-audit.json)
- [故障注入](evidence/fallback-injections.json)
- [checkpoint/release manifest](evidence/checkpoint-manifest.json)
- [测试、限制和失败工具 run](evidence/test-report.md)

## Gate 结果

| Gate / 指标 | 结果 |
|---|---:|
| 仓库测试 | `37 passed` |
| 真实 `GPPO-8.29@2a9bb9f` post-action Shadow 调用 | 12 次，PASS |
| belief/mask/graph version/action version/action submission 写入 | 全部 `0` |
| stale-before/stale-after/timeout/exception/OOD/high-uncertainty | 全部 zero-context |
| state-change ECE（raw/calibrated） | `0.07205 / 0.07205` |
| continuation ECE（raw/calibrated） | `0.10173 / 0.08284` |
| 50%/100% coverage state MAE | `0.03811 / 0.05565` |
| 完整 observe P50/P95/P99 | `5.69 / 6.99 / 8.05 ms` |
| synthetic OOD AUROC / recall | `1.0 / 1.0` |
| ID OOD false-positive rate | `8.59%` |

版本检查采用提交后两阶段合同：模型读取动作前的不可变 `graph_t` 和已确认的 executed action，但推理前后均核验
实际系统仍处于该动作提交后的 expected post graph/action versions。任何失败都不提交 candidate hidden，下一次有效
输入自动 history reset。

限制：OOD 仅由归一化特征 `+3` 的合成范围偏移验证，T-01 各 split 都包含相同七类 profile，不能据此声称真实
未知任务泛化。timeout 当前是推理完成后的 fail-closed 丢弃，不是硬中断 worker。T-04 完全不影响 GPPO 动作，
下游收益仍需 T-05 服务器/GPU 正式消融证明。

## 解锁

[T-05](../T-05/README.md) 已解锁。

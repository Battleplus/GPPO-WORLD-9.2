# T-04：Shadow、校准与风险门禁

**状态：blocked by T-03**

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

## 解锁

通过后解锁 [T-05](../T-05/README.md)。

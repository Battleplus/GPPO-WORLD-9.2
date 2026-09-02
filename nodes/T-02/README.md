# T-02：Graph World Model 基线

**状态：planned（T-01 已通过）**

## 目标

建立无自动事件头的动作条件异构图世界模型，先回答“模型是否真正学习 executed action 的后果”。本节点不修改 GPPO 策略。

## 模块

- typed graph encoder；
- executed-action encoder；
- temporal latent dynamics `[h_t, z_t]`；
- next graph/delta、reward、cost、continuation、uncertainty heads；
- 独立训练、评估、checkpoint 保存/加载与恢复。

## 对照

- last value / frequency；
- 等预算 summary-vector GRU；
- no-action；
- action-shuffle；
- graph world model。

## Gate

- checkpoint roundtrip 输出在冻结容差内一致；
- held-out 一步预测优于 T-00 冻结的朴素基线；
- 1/3/5-step 误差完整报告；
- action-shuffle/no-action 相对正确 action 显著变差；
- uncertainty 与误差风险呈可用的单调关系。

若 action shuffle 不影响结果，说明模型未使用动作条件，本节点不得通过。

## 保存点

每个 seed 保存 base-WM candidate manifest；节点通过时再指定 accepted checkpoint 和回退版本。

## 解锁

通过后解锁 [T-03](../T-03/README.md)。

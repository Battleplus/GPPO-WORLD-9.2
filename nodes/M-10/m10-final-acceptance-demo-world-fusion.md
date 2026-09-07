# 世界模型融合演示脚本（单独候选）

用途：证明已训练的 R2 world model 输出被 R3 融合策略实际消费，同时如实展示预测质量和触发负结果。它不是默认执行候选。

## 候选

- 策略：正式矩阵 `Graph-5 World / seed-1101` checkpoint。
- world model：R2 已训练并冻结的 `M10WorldModel` checkpoint；R3 没有重新训练 world model。
- context：R2 的 context head 与共享 backbone 通过 `context_mse` 获得监督梯度；R3 通过同一 snapshot 的 `_policy_input_bundle` 和最终复现的 context norm/调用记录验证消费。

## 演示步骤

1. 先展示 `prediction-audit-r3.json`：event BCE 0.258 对比同指标训练阳性率 baseline 0.166；done BCE 0.266 对比 0.221；全零 Brier 0.058 不和 BCE 直接比较。
2. 运行 `--fusion world`，展示每一步 world-model call、风险、context L2、策略动作及 policy version。
3. 说明 event 标签是下一环境决策间隔的 simulator consequence，不是已经验证的“未来需要重规划”标签。
4. 展示触发对照：risk threshold 0.1 每步触发、continuation 为 0；规则触发减少调用但任务效果从 return 19.500 降至 6.552，因此当前不默认启用 model-risk。

结论：预测输入融合已执行并被消费，但稳定收益未证明；当前可用默认仍是周期决策。


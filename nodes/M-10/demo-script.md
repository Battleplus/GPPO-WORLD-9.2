# M-10 历史演示脚本（保留）

> 当前总验收请使用 `m10-final-acceptance-demo-basic.md` 和 `m10-final-acceptance-demo-world-fusion.md`。本文件保留为历史 R/R2 演示底稿，旧指标和旧入口不代表当前最终候选口径。

1. 展示 `causal-acceptance.json`，说明未来事件不进入策略输入，延迟消息要等送达，stale snapshot 会被拒绝。
2. 运行：

```text
python tools/run_m10_causal_acceptance.py --output <new-run>/causal-acceptance.json
```

3. 指向 `ack_and_lease_progression` 和 `execution_truth_rejection`。强调 ACK 由执行传输处理，租约过期会回到 pending；隐藏能量可以让执行层拒绝，但不是策略直接读取真值。
4. 展示 `training-results.json` 的 5 个变体和 3 个 seed。先报完成数、过期数和 return，再报 seed CI；说明 MLP 结果较不稳定，world context 与 trigger 没有稳定提升。
5. 展示 `training-protocol.json`、`world-model-training.json` 和 Release。最后说明阈值 0.5 零触发的负结果仍在 v1 输出中，0.2 只是一组补充敏感性结果。

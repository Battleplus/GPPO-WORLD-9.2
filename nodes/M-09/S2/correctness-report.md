# 正确性与安全回归

优化前后使用同一 checkpoint、同一 60 条固定 tape 和同一确定性动作路径进行逐 tape 比较：

- action mismatch：0/60；
- logits mismatch：0/60；
- graph input hash mismatch：0/60；
- reward mismatch：0/60；
- 结束分类/任务完成/future-input mismatch：0/60；
- confirmation pipeline mismatch：0/60。

优化后的 S1-R2 服务器验收仍为 60/60，通过低置信度 payload 消费、SUSPECTED/CONFIRMED、过期、矛盾、stale、能量和版本约束。优化只改变推理上下文管理，不改变策略可见信息或执行层合同。

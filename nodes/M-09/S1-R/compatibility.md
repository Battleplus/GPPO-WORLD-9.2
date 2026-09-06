# S1-R 兼容性结论

S1-R 与三类型 GPPO-Adaptive checkpoint 保持兼容：17 动作、NOOP 和图字段维度未改变。能量、stale、deadline 和事件确认均作为执行/评估字段；它们没有被补零后伪装成旧策略输入。S1-R blocked 的原因是固定 tape 暴露的因果边界和低置信度确认不足，不是 checkpoint 加载失败。

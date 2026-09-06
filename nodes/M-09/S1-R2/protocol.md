# S1-R2 冻结判定规则

1. 原六类固定 tape、每类 10 条，共 60 条；不得替换失败样本。
2. 策略输入只包含当前决策上下文；动作执行过程中到达、step 返回时出现的 `new_events` 属于动作后观测，除非它们已在本次决策上下文中实际改变 graph/history/mask，否则不得计为未来输入。
3. 每个决策记录发生、到达、确认、决策开始、stale 重试、提交和 step 返回时间，以及 graph/action version、完整 graph hash、logits 和确定性动作。
4. 未来输入结论必须由配对案例支持：到达前未来事件不同但完整输入、logits、动作相同；合法到达/确认后允许输入与动作变化。stale 重试使用自己的上下文重新审计。
5. `confidence` 与 `severity` 是独立字段。payload 中的 confidence 必须进入原始 observation，并由 detector 消费；不能用事件名或 payload 存在代替行为证据。
6. 直接确认阈值保持 0.95。低于 0.95 的正证据不能走单源直接确认；Region vacancy 至少需要两个不同来源的正证据，Target/Destroyed 仍服从其更高的原有来源数要求。证据不足为 SUSPECTED，超时为 EXPIRED，矛盾为 FALSE_ALARM。
7. 原 60 条与新增专项 fixture 分开汇总。人工执行层探针不计入自主策略完成率。

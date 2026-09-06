# S1-R 修正协议

## 生命周期计数

每条 trace 同时记录 `episode_ended`、`task_completed`、`task_failed`、`infeasible`、`deadline_timeout` 和 `end_reason`。episode 结束由 `terminated || truncated` 得出；任务完成来自环境的 `pending_regions`、`event_queue`、目标真实状态和紧急事件状态。`terminated` 不能代替任务完成。

## 提交约束

初次提交和 stale 重试均经过 `EnergyLedger`。环境先判定 stale，再提交实际接受的动作给 ledger 扣费。拒绝动作不扣费，重试重新读取能量并按新 UAV 扣费；重复 submission id、stale、非法动作和能量不足都返回独立状态。每次尝试记录 `energy_before`、`energy_after`、`charged_uid`、`executed_action` 和原因。

## 因果边界

策略图字段使用白名单；事件记录属于评估证据，不自动视为策略输入。只有本次 `new_events` 实际暴露且 `observed_at > decision_time` 时计入未来输入违规。trace 同时保存发生、可见和决策时间，未用字段名称扫描代替时序检查。

## 场景断言

紧急任务必须有真实到达、到达后的响应、真实完成和 deadline 满足。复合扰动要求单机损毁、通信 stale 和低置信度事件均有实际状态/时序证据；事件名称或 payload 不能单独通过低置信度断言。人工执行层探针单独报告，不混入自主策略完成率。

固定 tape、checkpoint、服务器路径和运行环境保持 S1 锁定值；没有新增训练。

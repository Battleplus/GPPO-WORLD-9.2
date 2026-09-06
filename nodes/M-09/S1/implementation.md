# S1 实现与边界

当前冻结基线的真实实现已经提供 17 动作、NOOP、版本化提交、UAV 损毁、目标发现/损毁、
区域空缺和弱通信事件。S1 协议把能量和紧急任务定义为执行层/评估层扩展，不改变旧
策略输入和 checkpoint 兼容性。

S1 工具 `tools/run_s1_functional_acceptance.py` 在冻结环境外包裹执行层：紧急任务通过
带 deadline 的 tape payload 表示，能量不足拒绝边动作并执行 NOOP，通信事件通过旧环境的
版本化提交触发 stale 拒绝和重试，复合场景固定损毁、延迟通信和 0.55 置信度三个因素。
这些字段没有送入旧策略图；工具逐决策记录 proposal、execution、事件、回退和安全计数。

S1-A 的第一次运行确实失败，随后隔离环境复现成功；失败详情保留在 [failed-records.md](failed-records.md)。

返航、换电、充电、五类型图、世界模型新训练和延迟优化均不属于 S1。

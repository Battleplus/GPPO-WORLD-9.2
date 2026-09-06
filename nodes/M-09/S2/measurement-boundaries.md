# 计时边界与运行链路

单次决策的外层 `decision_wall_clock` 从调用 `begin_decision()` 前开始，到日志行 JSON 序列化完成结束。它包含下列子段，但子段不可直接相加替代外层：

1. `graph_decision_context`：构造当前 graph 和决策版本。
2. `feature_tensor_prepare`：必要的 graph tensor 准备/设备传输；CPU 为零成本路径。
3. `policy_forward`：模型前向；GPU 前后同步。
4. `action_selection_legality`：确定性 argmax、NOOP 合法性处理。
5. `in_flight_advance`：通信/复合 tape 的显式执行中时间推进。
6. `submit_execution_total`：版本检查、动作提交、能量/执行层约束、事件确认、环境推进及返回 graph。
7. `environment_progress`：`_step_current` 内部执行的嵌套测量，用于定位 submit 内部成本。
8. `retry_*`：stale 拒绝后的重试上下文、前向、选择和提交，单独统计。
9. `logging_serialization`：本次原始日志行的 JSON 序列化，不包含离线断言或归档压缩。

另行记录 `episode_wall_clock`（reset 到 episode 结束）和冷启动模型加载时间。仿真时间字段不参与墙钟统计；S1-R2 离线验收和 Release 压缩不计入模型推理。

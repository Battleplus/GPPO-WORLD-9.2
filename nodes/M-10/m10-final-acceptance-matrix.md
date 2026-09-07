# M-10 会议要求—证据总表（总验收候选冻结）

日期：2026-09-07。本文是当前交付口径；M-09、M-10、M-10-R、M-10-R2、M-10-R3 的历史报告和 Release 不改写。

## 逐项映射

| 会议要求 | 实现入口 | 实际运行 | 制品 | 当前结论 | 剩余限制 |
|---|---|---|---|---|---|
| 基本任务分配 | `M10Environment`、`TaskDecisionBridge`、`TaskExecution` | 服务器组件/因果测试；最终候选复现 | `causal-acceptance*.json`、final-repro | 仿真功能已验证 | 未做真实飞行、生产认证 |
| 紧急新任务 | `TaskLifecycle` 到达、已收到 task telemetry、`task_arrival` 触发 | 到达/版本/mask/ACK 路径测试 | R2/R3 测试与轨迹 | 仿真功能已验证 | tape 是冻结合成分布 |
| UAV 损毁 | `ServiceClock` damage、确认故障标志、fencing | 损毁及恢复因果路径；final-repro `uav_damage` | R2/R3 服务器证据 | 仿真功能已验证 | 未覆盖真实故障率与控制器 |
| 能量不足 | 服务能耗和执行拒绝 | 隐藏真实能量导致拒绝的隔离测试；final-repro `energy_insufficient` | R2/R3 测试与轨迹 | 仿真功能已验证 | 能量真值不进入策略特征；返航/换电/充电范围待确认 |
| 通信中断/恢复 | `ServiceClock` disconnect/reconnect、telemetry delay | 断链、恢复、lease/ACK 路径 | R2/R3 测试与轨迹 | 仿真功能已验证 | 未验证真实网络协议和控制周期 |
| 世界模型训练 | `train_world_model`；R2 `context_mse` | R2 已实际预训练；R3 冻结 checkpoint 审计，未重新训练 | `world-model-training-r2.json`、R2 Release | 新训练已执行 | event label 仍是下一步 simulator consequence，不是已证明 replan label |
| 融合策略消费预测输入 | `M10ActorCritic.context_projection`、`_policy_input_bundle` | R3 融合策略已训练；最终 fusion 复现记录 context norm/调用 | R3 formal matrix、final fusion repro | 预测输入实际被消费 | 未证明稳定收益或部署适用性 |
| 公平对照 | 同 tape、动作、奖励和环境协议 | 5 变体×3 seed×8192 env steps，128 optimizer updates/seed | `training-results-r3-summary.json`、formal matrix | 已形成描述性对照 | 3 seed/有限 tape，不支持显著性或普遍性结论；7 项旧 baseline skip |
| 触发机制与成本 | 语义事件、安全门禁、最大等待、model-risk | 同一 World checkpoint/tape 的 periodic/rules/model-risk 对照 | `trigger-comparison-r3.json`、server evidence | 负结果可信：risk 每步触发；规则省调用但效果下降 | model-risk 不是默认候选；真实控制周期未知 |
| 端到端延迟 | 观测、world、触发判断、actor、门禁、同步、环境推进 | 服务器 CPU/CUDA 归一化仿真测量，保留原始样本 | R3 latency artifacts | 已测量并可复现 | 非网络/实飞测试，不宣称竞赛实时达标 |
| 训练文件与复现 | 配置、seed、tape、checkpoint、恢复状态、日志 | R2/R3 归档已校验；本轮只新增无训练候选复现 | R3 Release + final acceptance Release | 可追溯交付 | 大型训练归档通过旧 Release 索引，避免重复上传 |
| 汇报材料 | PPT、讲稿、演示脚本、FAQ、限制 | 本轮更新并校验 deck；群发/彩排/导师评审未进行 | final acceptance slides/docs | 材料已准备 | 人工汇报活动待用户执行 |

## 状态分层

- **仿真研发与实验交付：** 已验证/已归档。上述功能、R2/R3 训练和 R3 评估都有独立入口与制品。
- **算法稳定收益：** 未证明。World 在当前正式矩阵为 `32.156 ± 2.179`，没有超过 MLP-2 `32.445 ± 1.785` 或 Graph-2 `32.424 ± 1.777`；这是有限矩阵的描述性结果，不是“任何场景都无改善”。
- **真实部署验证：** 未验证。服务器结果是归一化仿真和指定环境延迟测量。
- **用户范围：** 待确认。返航、换电、充电是否为最低验收，竞赛任务规模和真实控制周期均未自行填入。
- **人工汇报活动：** 未举行。群发、彩排和导师评审不在本轮已完成证据中。
- **`full_goal_complete`：** `false`，因为范围与真实部署/人工活动仍有未闭合项。

## 候选冻结

默认演示候选为正式矩阵中的 `MLP-2 Base / seed-1101` checkpoint；依据是固定矩阵内最高描述性平均 return（32.445）和最高吞吐（142.9 steps/s）。这是工程演示选择，不是预注册、无偏的模型选择，也不改写科学比较。融合演示候选为 `Graph-5 World / seed-1101` 加 R2 冻结 world checkpoint，仅用于展示预测 context 被消费及其效果边界；不默认启用 model-risk 触发。

“三重原子攻击”在当前仿真中统一称为**三因素复合扰动压力测试**：同一冻结 tape 可组合单 UAV damage、communication disconnect/reconnect、低置信度观测/风险门禁条件。低置信度是策略输入与门禁条件，不是额外外部故障；对象、时间、持续时间和是否同时发生以 tape 为准，不能外推为生产保障。


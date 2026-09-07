# M-10 历史声明与证据边界（保留）

> 当前总验收的逐项映射见 `m10-final-acceptance-matrix.md`。本表保留历史阶段声明；涉及 R3 指标、world context 训练事实和候选冻结时，以当前总表及 R3 报告为准。

| 声明 | 适用范围 | 证据 | 分类 | 禁止扩大 |
|---|---|---|---|---|
| 任务到达、服务进度、deadline、损毁、断联和能量扣费进入同一环境时钟 | M-10 归一化仿真，4 UAV、6 槽 | `gppo_world/m10_environment.py`、`causal-acceptance.json` | 已完成 | 不等于真实飞控或网络 |
| 策略只读已收到消息，未来任务和事件不进入公开快照 | 默认 telemetry delay=0；延迟验收另测 | `causal-acceptance.json` 的 future/delayed checks | 已完成 | 不外推到真实链路完整性 |
| ACK、版本和租约约束执行 | M-10 TaskExecution 接入 | `causal-acceptance.json`、`gppo_world/task_execution.py` | 已完成 | 不把 bridge 组件测试扩展成生产执行保证 |
| MLP、Graph、History、world-context、event-trigger 均实际训练 | 5 变体×3 seed×1024 steps | `training-results.json`、训练归档 `output/checkpoints/` | 已完成 | 不把短预算结果写成稳定收益 |
| Graph 在本协议下完成数均值高于 MLP | seed 1101/2203/3307，固定评估 | `training-results.json` | 受限观察 | CI 较宽，不能宣称算法普遍优越 |
| 世界模型融合提升效果 | 同一协议 | `training-results.json` | 未证实 | world context 完成数均值仍为 4.0 |
| 事件触发优化效果 | threshold 0.2 补充矩阵 | `training-results.json` 及 threshold 0.5 v1 | 未证实 | 0.5 零触发，0.2 属敏感性分析 |
| 139 passed、7 skipped | 服务器源码归档，旧 GPPO baseline 缺失导致 skip | `server-pytest-final.log` | 已完成 | 不写成 146 passed |
| 两个历史 Shadow timeout 在服务器通过 | Python 3.10.12/Torch 2.2.2 受控复跑 | `server-shadow-recheck.log` | 已完成 | 不归因于机器负载，不改 50ms 门槛 |
| 已完成五类型真实系统 | 本轮 five-type 只是同一公开数据的编码视图 | `limitations.md` | 明确撤回 | 缺失真实五类型资产 |

返航、换电、充电范围、竞赛控制周期和人工评审仍待确认或未发生。

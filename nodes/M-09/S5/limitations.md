# S5 限制与未完成研究

## 能力边界

- 当前交付是 UAV/Region/Target 三类型图，实体规模 4/4/3，17 个离散动作；不存在可宣称的五类型 Task/Event 图。
- NOOP 是等待，不是返航、换电或充电；当前没有完整的业务 Task deadline 字段。
- 能量不足、损毁和通信证据本轮主要验证执行/确认/回退边界，不等于策略已通过专门训练学会这些语义。
- 世界模型永远不直接提交动作；A 的 Shadow 是纯 side-car，B 的 adapter 也必须经过真实 action mask、version、ACK/lease/fencing。

## 证据边界

- S4 的 635 decisions 是 B 历史 EAWM-GPPO；577 valid、58 fallback、487 adapter-used 的定义和来源已逐 trace 重算。它不是 A 的 60 tape，也不是 S3 pure GPPO 的新训练结果。
- timeout 是 post-inference gate，不是同步推理硬取消或真正 bounded-return 保证。
- OOD 分数 269.0106024867358 来自 synthetic feature-range shift；不能扩展到生产未知任务泛化。
- S2 的延迟改善只适用于协议中的硬件、模型、图规模和运行时；没有新的控制周期，因此没有实时合规结论。
- 本次服务器环境是已安装环境复用，未宣称任意新机器可自动安装；GPU 空闲状态只是检查时刻，不是资源预留。

## 未完成研究

- 取得并冻结会议五类型源码、模型和数据合同。
- 完成 GPPO-History、普通 PPO、三类型/五类型在同一输入、规模、控制周期和多 seed 下的公平比较。
- 重新判断历史 EAWM 的 context 是否改善真实 held-out return 和安全指标；不能用 predicted return 替代真实环境结果。
- 设计真实 OOD、可取消/有界推理和长时间故障恢复测试。
- 只有在上述输入和研究问题冻结后，才考虑新增训练或 T-06 短期 imagined rollout。

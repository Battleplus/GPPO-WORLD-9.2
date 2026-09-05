# 任务、节点、事件与测试术语

## PPO、GPPO、GPO

- **PPO**：仓库训练器实现的 clipped Proximal Policy Optimization；它是优化算法，不规定输入必须是图或向量。
- **GPPO**：本项目对图策略的名称。`GraphActorCritic` 用关系感知图层编码 UAV/Region/Target，再在 UAV–Region 候选边和 NOOP 上输出策略；训练仍使用 PPO 更新。
- **会议中的 GPO**：仓库没有名为 GPO 的独立算法、类、配置或 checkpoint。S0 不把它自动等同为 GPPO；在取得会议版本前，写作“会议所称 GPO（实现未定位）”。

## 节点类型与实体数量

“三类型”指 schema 中有 UAV、Region、Target 三种 node type；“4/4/3”是当前每类实体数。它们是不同维度。当前动作数 17 也不是节点数，而是 `4 UAV × 4 Region + NOOP`。

| 概念 | 当前代码语义 | 是图节点 | 进入策略输入 |
|---|---|---:|---|
| UAV | 有位置、存活/传感器状态、当前任务枚举、区域负载和跟踪目标 | 是 | 是，节点特征及关系特征 |
| Task | UAV 的 `SEARCH/TRACK/IDLE` 状态；策略只分配搜索 Region，TRACK 由事件规则触发 | 否 | 是，作为 UAV one-hot 特征；没有独立 Task 节点/边 |
| Region | 搜索责任单元，含中心、优先级、工作量、空缺时长、负责 UAV、pending/合法状态 | 是 | 是，节点和 UAV–Region 动作边 |
| Target | CAR/COMMAND 实体，含发现、跟踪、摧毁、区域和 tracker 状态 | 是 | 是，Target 节点及 located/tracked 关系 |
| Event | 可重放外生事件记录；含 occurred/observed 时间、对象、severity、版本等。世界模型还生成 ordinal/nominal/structural/evidence 监督标签 | 否 | 不作为节点；确认后的状态变化间接进入图，历史 evidence 进入世界模型数据路径 |

会议所述 UAV/Task/Region/Target/Event 五类型实现未找到。要变成真正五类型，必须定义 Task/Event 的节点生命周期、特征、边、padding/mask、动作语义和 checkpoint 兼容规则，并重新训练；不能通过更名现有字段得到。

## 动作、合法性和结束条件

实际动作空间是 17 个离散动作：前 16 个按固定顺序表示 `(uav_id, region_id)`，最后一个是 NOOP。只有 pending Region 可以变更；UAV 必须存活、传感器可用且未处于 TRACK。无 pending Region 时 NOOP 合法；有 pending 但无可用 UAV 时 NOOP 也合法，用于等待未来释放。环境会修复非法索引/被 mask 动作并累计 `repair_count`；版本或执行链拒绝的提交降级为 NOOP，且不能改变环境。

一次事件影响的所有 Region 获得合法负责 UAV 后，事件 resolved。所有可见事件耗尽且 pending/event queue 为空时完成；pending 无合法边但未来存在 TARGET_DESTROYED 释放事件时是 temporary infeasible；没有未来释放时是 final infeasible 并终止。超过 `max_decision_steps` 或 `max_time` 是 truncated/超时。这些是环境结束语义，不等同于业务 deadline；当前没有逐 Task deadline 字段。

## 四类会议扰动的支持核查

| 扰动 | 当前真实支持 | 处理决定 |
|---|---|---|
| 紧急新任务 | **部分。** `TARGET_DISCOVERED` 会把 UAV 从搜索转为跟踪并释放 Region；`REGION_VACANCY` 会产生重分配。但没有独立 Task 实体、通用任务注入、任务 deadline 或明确紧急优先级队列 | S1 新增/冻结可控场景，不能把现有事件直接标成完整支持 |
| 节点损毁 | **已实现 UAV_DAMAGE。** UAV 变为不可用，释放搜索 Region，mask 排除该 UAV；有 detector/confirmation 路径 | S1 对此做 10 条功能验收，不在 S0 复报结果 |
| 能量不足 | **未实现。** UAV 实体和图特征没有 battery/energy；动作和终止条件无能量约束 | S1 必须实现或明确从中旬演示降级；现模型需评估输入兼容性，可能重训 |
| 通信中断 | **底层部分实现。** detector 支持丢包、重复、乱序和 source partition，状态机支持心跳缺失/探测/恢复，执行链有 ACK/lease/fencing；当前三类型图仅以 UAV–UAV communication quality 特征表示通信质量 | S1 建立可控持续时间和恢复场景并验收；目前不能宣称完整端到端通过 |

换电池、返航和充电动作均未找到。NOOP 只是等待，不等于返航或换电。

## “三因素复合扰动压力测试”

仓库中未找到“三重原子攻击”的具体测试类、场景配置或结果；该名称弃用。规范名称为**三因素复合扰动压力测试**：

1. **单机损毁**：指定一架当前可用 UAV 在 `t=10s` 发生真实 `UAV_DAMAGE`，severity=1.0；通过检测/确认链到达策略，确认后该 UAV 不得接受有效分配。
2. **通信异常**：从 `t=8s` 到 `t=20s` 对损毁 UAV 的健康来源启用 partition，并冻结 loss/乱序参数；需记录每条 evidence 的 emitted/received/confirmed 时间和恢复消息。当前存在底层机制，尚缺统一复合场景控制入口。
3. **低置信度**：在 `t=9s` 注入同一损毁对象的非权威 0.55 置信度观察。其含义是证据不足，不能单独当作确认后的真实损毁；当前 detector 能生成 0.55 观察，但缺少 S1 冻结注入接口与完整复合测试。

冻结顺序为通信异常开始 → 低置信度观察到达 → 真实损毁发生 → 后续证据到达/确认 → 通信恢复。`occurred_at` 是触发时刻，`received_at/confirmed_at` 是策略可见时刻；策略只允许对已经确认并写入 belief 的变化响应。建议严重程度和持续时间使用上述固定值作为 S1 首版配置，属于**建议**，不是已执行结果。

测量从通信异常 `t=8s` 开始，到所有受影响 Region 恢复合法分配且通信恢复，或达到 episode `max_time` 为止。预期合法行为：确认前不偷看真实损毁；确认后不向损毁 UAV 有效提交；仅从当前 mask 选边或 NOOP；版本过期提交被拒绝；资源不足可明确 temporary/final infeasible。失败标准：任何未来信息使用、确认后对损毁 UAV 的有效提交、绕过 mask/version/ACK/lease/fencing、未解释终止/超时，或观测条件无法按冻结配置重放。

上述三因素组合当前状态是**待实现、未执行**，不存在 S0 测试结果。

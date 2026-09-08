# M-10 恢复任务可观测性与可行机会验收

## 结论先行

本轮不训练、不启动 B/C、不重跑完整课程，也未修改历史 pressure tape。工作基于阶段二已归档的 checkpoint/validation 证据，并新增独立的恢复机会候选池；候选池由现有合法公开信息调度器通过完整 M-10 执行链筛选。

* 阶段二训练 artifact 的 `per-seed` 记录是检查点 validation 评估，不含训练 rollout/event ledger；因此训练中的恢复机会、成功样本数为 **未知**，不能用 validation 的 96 个机会代替。
* 原 37 例“任务必需遥测缺失/过期”逐例复放后，0 例是静态任务描述从未发布；37/37 在故障获知边界至少有任务字段消息被接收，但该边界的一个或多个字段已 stale。25/37 含动态字段（deadline、pending、priority、remaining_service）stale；15/37 在合法故障获知边界已经没有正 deadline 余量。两项可重叠。
* 新候选池每 split 64 条（recovery/composite 各 32），参考调度器合格 42–50 条；确定性选取每 split 8 条（各 profile 4 条）。选中 4 split 共 32 条均通过真实 fault telemetry、公开 mask、alternate command、ACK、lease 维护、移动、服务和 deadline 完成。
* 旧 Graph-5 Base seed-1101 checkpoint 在同一新候选 tape 上完成 32/32；这是修正机会集上的环境/旧模型复评，不是新训练收益，也不是原压力分布总体表现。
* 结论仍不等同于弱通信可用性通过：原压力场景和阶段二恢复门槛仍未通过。新机会集证明了“存在真实合法信息路径和足够时间的恢复任务”，但没有证明策略已学会一般恢复。

## 版本、保护与范围

* 本地隔离工作区基线：`3fd10e06c67cac708232d01ed60290309928d9e8`；用户报告远端分支提交：`bf1aa1a8cc708e94c2a3b3baa14eb4cc703a9017`。本轮不 reset、不 force push、不修改 main、历史 Release 或并发主工作树。
* 服务器只使用新目录 `/home/user1/m10-runs/20260908-recovery-observability-v2`；阶段二输入目录只读使用，没有修改共享环境或停止其他任务。复核结束时没有 M-10 训练进程，GPU 空闲。
* 本轮唯一运行时源码改动是给 dropped telemetry 审计记录补充 `entity/field/sequence/measured_at/received_at`；丢包决定、策略输入、mask、ACK、lease、fencing 和 deadline 语义不变。该改动使“生成后丢弃”可与“未生成”逐字段区分。

## 指标与分母核对

| 对象 | 分母/分子 | 口径 |
|---|---:|---|
| 阶段二原恢复记录 | 1/8、0/11、3/12 | 旧函数只把已经出现 alternate accepted handoff 的事件纳入，历史保留但不能称完整恢复率 |
| 修正 pressure attribution | 策略 1/96；参考 0/84 | 每个 damage/disconnect 与实际被中断 travel/service 任务配对；无 handoff 也入分母 |
| 训练恢复样本 | 未知 | artifact 没有训练 rollout/event ledger；validation episode 不是训练样本 |
| 新条件课程 | 参考 32/32；旧 checkpoint 32/32 | 仅对参考执行成功的候选条件筛选，属于 conditional curriculum，不是 pressure 分布成功率 |

“固定状态参考接管 4 个、增量挽救 0 个”与“策略 1/96”不能合并：前者是从策略故障获知边界深拷贝状态后替换控制器的分支结果，4 个目标在原策略分支也已完成；后者是全 episode 策略分支按修正事件—任务分母统计的完成数。成功定义均为故障后相关任务产生有效服务并在 deadline 前完成。

## 37 例可观测性专项

检查位置是每个策略分支第一次合法收到 `alive=0`/`connected=0` 故障遥测后的决策边界。字段分为静态 `x/y/region_id/target_id` 与动态 `deadline/pending/priority/remaining_service`。

| 观察 | 数量 | 解释 |
|---|---:|---|
| 静态字段从未知道 | 0/37 | 未发现“任务描述发布责任完全缺失”的证据 |
| 至少一个字段 stale | 37/37 | mask 合同按字段 freshness 关闭候选是预期安全行为，不能直接判为代码错误 |
| 含动态字段 stale | 25/37 | 动态状态通常决定 pending/剩余服务/deadline 是否可接管 |
| 仅静态 freshness 仍阻断 | 12/37 | 字段已知但超出 `telemetry_max_age`，仍不能作为当前真值使用 |
| 获知时 deadline 无正余量 | 15/37 | 通信等待与故障后的时间预算已耗尽；不应通过放宽 deadline 修复 |
| 故障后至获知边界至少有接收任务消息 | 37/37 | 不是“消息从未产生”的证明；具体字段、时序和消息状态见 detail JSON |

当前发布责任来自 `M10Environment._deliver_observations`：任务字段由 simulator/controller-side observation path 广播，不依赖受损或断联 UAV 发布。故障和任务状态只在 ServiceClock/执行端产生，策略只能消费已送达且仍 fresh 的 `TaskPolicyView`。本轮没有从隐藏状态刷新 view，也没有加入无条件 task-release、无限 TTL 或绕过 ACK/lease 的旁路。

因此 37 例的证据分类是：没有确认 A 类 publisher 缺失；主要是 C 类通信压力下 freshness 下降，并与 B 类“到达时已无足够时间”共同出现。具体事件仍需按消息账本解释，不能把每一例都简化成同一原因。

## 合法恢复信息路径

本轮冻结并验证的路径为：故障由 ServiceClock 真实作用于执行中的 UAV → 下一次 observation 通过既有 telemetry link 发送 affected UAV 状态及任务状态 → `CommunicationProfile` 决定 delay/loss/outage/duplicate/reorder → `ReceivedTelemetry` 按 sequence/version 去重和拒绝旧值 → `TaskPolicyView` 仅在字段 known 且 fresh 时开放 mask → controller 提交 alternate UAV–Task command → command 到达、ACK、version、lease、fencing 和 energy gate 全部通过 → alternate UAV 移动并服务。

该路径使用的消息身份、接收时刻和测量时刻都保存在通信账本中。dropped telemetry 现在也保存 `entity/field/sequence`，可以从消息账本区分“生成后丢弃”和“未生成”。本轮没有改变协议强度；如果后续需要 task-release 查询/重传，应另行版本化，设置消息 ID、最大重传次数和有效期，并使查询、回复、ACK 都经过相同链路模型。

## 新恢复机会课程

每条候选保持原 Graph-5 动作容量（4 UAV、task capacity 6、每周期最多一个新命令）和原 reward/执行门禁；候选本身使用 1 个任务，以证明恢复链而不是用任务拥塞掩盖通信问题。任务由 `uav-0` 在 travel/service 中执行时发生一次 damage 或 disconnect；disconnect 保留 reconnect 事件。候选包含 `recovery`（单一 outage）或 `composite`（延迟、随机 loss、乱序、outage、command/ACK loss）profile。

候选只在以下全部满足时进入 selected tape：

1. 故障确实中断 affected UAV 的 travel/service；
2. fault telemetry 在合法接收路径到达，且 `measured_at >= event_time`；
3. received-only mask 出现具体 alternate UAV–Task 候选；
4. alternate command 实际接受并收到所需 ACK；
5. post-event service 实际发生，且任务在 deadline 前完成；
6. 重复、越权、fencing 等安全拒绝为零。

每个 split 的候选池 64 条、合格数及筛选率如下。筛选率是候选课程构造成本，不是原压力分布失败率。

| split | pool | eligible | filter rate | selected |
|---|---:|---:|---:|---:|
| recovery-opportunity-train | 64 | 44 | 31.25% | 8（recovery 4/composite 4） |
| recovery-opportunity-validation | 64 | 50 | 21.875% | 8（recovery 4/composite 4） |
| recovery-opportunity-test | 64 | 44 | 31.25% | 8（recovery 4/composite 4） |
| recovery-opportunity-ood | 64 | 42 | 34.375% | 8（recovery 4/composite 4） |

这些是条件课程分布：每个 split 的 test/OOD tape 已生成并冻结，但本轮没有用模型结果或 test tape 选择 checkpoint/阈值。原 validation/pressure tape 继续作为诊断回归，不被替换。

## 新 tape 复评

服务器与本地生成器输出一致。参考调度器和旧 Graph-5 Base seed-1101 都在 selected 32/32 条上完成；每条都经过真实环境的移动、服务和租约维护。该结果回答“环境是否存在可执行恢复路径”，不回答“旧策略在原压力分布是否可用”。

服务器 opportunity audit SHA-256：`3e256bcbb7a15d4c1986ac84fbca8c6f896ab20aba5608337d7bc339da3ce36b`；服务器 detail audit SHA-256：`35883315890fc4550574bce764a04ea44f79da5664a9ef7b19775c4053f3cf28`。完整 JSON 归档中保留逐候选通信、执行、clock、任务状态和筛选失败原因。

## 训练入口核对

阶段二每个 seed 有 8 个 checkpoint records、16,384 新环境步；每个 record 含 64 个 validation episode，三个 seed 合计 1,536 个 validation episode exports。没有 `transitions`、rollout ledger 或训练事件逐步记录。本地针对性回归为 21 passed；修正 dropped telemetry 字段后，独立 basetemp 下本地全套为 **154 passed in 7.43s**，服务器针对性新增测试为 **4 passed in 0.81s**。因此：

* 训练恢复机会总数：未知；
* 训练恢复成功样本：未知；
* 96 个机会：仅来自冻结 composite validation checkpoint 复放；
* 新 32 条 selected tape：课程候选和复评证据，不是训练结果。

## 下一步决策

本轮具备启动下一步 A-only 有界学习能力实验的前置条件：新课程存在真实合法恢复轨迹、公开候选和执行时间；奖励/动作/安全合同没有被本轮修改；训练机会可通过新 train tape 显式计数。但本轮不自动启动训练。若用户确认进入下一步，最小假设应是“在相同 reward 和安全合同下，增加可审计恢复机会后，策略能否学会从公开候选选择接管”，并预先冻结环境步数、验证门槛和失败停止条件。

弱通信原压力可用性仍为未通过；B/C 未启动。返航/换电/充电、真实控制周期和人工汇报活动仍单列待确认。

独立归档：[m10-recovery-observability-v1-20260908](https://github.com/Battleplus/GPPO-WORLD-9.2/releases/tag/m10-recovery-observability-v1-20260908)，目标提交 `74078b53e4b566ad08780d79221b93f6e83373bf`。最终资产名称与 digest 以 Release 页面为准；首个上传包保留，不覆盖历史 Release。

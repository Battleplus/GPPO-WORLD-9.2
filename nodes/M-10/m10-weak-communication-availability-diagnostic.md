# M-10 弱通信可用性诊断与恢复验收

日期：2026-09-07。运行目录：`/home/user1/m10-runs/20260907-weak-comm-diagnostic-v1`。本报告暂停新增训练，只做当前冻结 tape 的链路诊断、合法可行性阶梯和必要的审计修正；不改写 M-09、M-10、M-10-R/R2/R3、弱通信 Release 或原始负结果。

## 版本与证据边界

本地起始核查分支为 `execute-r02-20260905`，HEAD 为 `6da0a3b`（`6da0a3ba8c6c4c22e271dc9f1e959d552b66be87`）；远端起始头为 `1f28b57279c07ccf00d0e7058731a30e4a1513b5`。本轮诊断归档以非 force 方式快进远端，最终文档头为 `00f1aec31a15cbbfad3049860aef4ae2631e6c48`；本地 worktree 因已有并发 commit 进程未强行改写。未跟踪的构建/pytest scratch 目录保持原样。历史弱通信 Release `m10-weak-comm-gppo-world-v1-20260907` 保留不变。

服务器专用诊断目录已实际执行，无训练进程：`/home/user1/m10-runs/20260907-weak-comm-diagnostic-v1`。诊断 JSON SHA-256 为 `2b068e9975823dafcba8c01cd9f83f12ea5850a0f77635f1d8974221824fec20`，服务器合同审计文本 SHA-256 为 `6ee1dc976a3352adb69d62ce1300816e418eb53504d050b204aaeb3e84518b70`。当前源码的服务器直连弱通信合同审计为 `11 passed`；服务器环境没有 pytest，因此不把该数字冒充 pytest 全套。本地使用受控新 basetemp 的全套为 `171 passed`。此前 Release 对应的历史口径为本地 `167 passed`、服务器直接审计 `9/9`；加入过期遥测测试后的历史最新口径为本地 `168 passed`、服务器直接审计 `10/10`；本轮消息账本相关集为 `11 passed`，新增诊断直连测试 `2 passed`。这些数字属于不同源码/测试集合，不能混写。

## 固定失败 tape 的完整链追踪

使用既有弱通信 `final_test` tape 首个 episode、Graph-5 Base seed-1101 checkpoint，在服务器无训练确定性推理。17 个决策步中：

| 链环节 | 实证结果 |
|---|---|
| 任务到达/遥测 | 策略视图起初无有效候选；随后多个时刻出现合法 mask。遥测账本为 1,144 个原始 wire message ID，其中 782 sent、362 link dropped、701 delivery accepted；没有把重复/过期 delivery 混入原始发送数。 |
| actor 动作 | 17/17 次均选固定 NOOP action `24`，即使第 2、4、7、8、10、11 步等出现合法候选。 |
| 命令/版本/bridge | 17 个 command sent；均为 NOOP，0 个具体 UAV–Task proposal 进入 `TaskExecution`，因此没有 stale/版本拒绝证据。 |
| ACK/lease | ACK `0`，accepted command `0`，lease `0`。 |
| 移动/服务/结算 | 没有 travel 或 service；只有 idle 能耗。最终 6 个任务 expired，completed `0`。 |

因此当前近零完成的首要、已被逐步日志直接证明的原因是：冻结策略没有在可见合法候选出现后发出具体分配动作；不是已观察到命令普遍因版本 stale 被拒绝。弱通信的延迟/丢包和 freshness mask 确实减少了早期决策机会，但它们不能解释后续仍连续 17 次 NOOP。原正式训练/评估的“低完成负结果”仍有效，但能力声明必须收窄为“实验执行完成、该策略在该 tape 上不可用”，不能称为弱通信任务处理可用。

## 合法可行性阶梯

同一 16-episode final tape、96 个到达任务，使用只读取已送达公开快照/mask 的确定性调度器；每次新分配仍经过相同 bridge、版本、ACK、lease、fencing 和真实 ServiceClock，非重规划只续用同一 lease。它不是模型优势基准，也不是全知上界。

| 级别 | 合法调度器完成任务 |
|---|---:|
| ideal | 42/96 |
| telemetry-delay | 19/96 |
| random-loss | 30/96 |
| burst-loss | 29/96 |
| reorder | 22/96 |
| recovery | 29/96 |
| composite | 21/96 |

完整 tape 的合法调度器仍受当前单动作/单活动续租接口、移动时间和紧 deadline 影响，故不能从 42/96 推出所有任务物理可行；它足以证明环境存在真实分配、移动、服务和完成路径，也证明“所有失败都由通信合同导致”不成立。最小场景进一步隔离：一架 UAV/一任务在 ideal、延迟、随机丢包、burst、乱序和 recovery 均完成；复合级别在单 UAV、deadline 8 的紧场景为 0/1，说明复合通信与可见 freshness 会使该特定时间预算不可行。两架 UAV、一任务、uav-0 在 1 秒断联、4 秒恢复时，合法调度器能由另一架 UAV 接管并完成 1/1；这证明损毁/断联后的“其他合法资源恢复服务”路径真实存在。源 UAV 复活不计作恢复。

## 通信账本与时间语义

本轮为 Telemetry 增加稳定 `message_id`，重复投递保留同一 ID、以 `delivery_ordinal` 区分。对遥测：`original_wire_attempts = sent + link_dropped`；delivery outcome 是 `received + stale_or_duplicate + expired`，后者可包含重复投递，属于嵌套而非互斥发送分类。命令和 ACK 仍用 command ID；ACK 丢失不撤销执行端已经接受的一次命令。

审计保留 `measured_at`、`received_at` 和实际调度时刻；当前实现的命令 transport 在 `step` 内同步抵达 bridge，故没有“遥测之后又自动更新导致命令到达必 stale”的证据。消息过期会记录 `expired` 且不进入视图；乱序旧 sequence 不覆盖新状态。该结论限于当前仿真合同，不能外推真实网络。

## 结论与修复决策

1. **为什么完成接近零？** 已证实的直接原因是 Graph-5 Base seed-1101 在合法候选出现后仍 17/17 选 NOOP，未产生任何具体分配/ACK/lease/service；弱通信只放大了可见候选延迟和时间损失。完整多任务负载还受到移动、deadline 和单活动续租接口约束。
2. **合法调度器能否完成和恢复？** 能在最小场景及各单因素级别形成真实服务；两 UAV 断联恢复场景能由另一 UAV 接管。完整 tape 的完成数为 19–42/96，不能宣称全场景可用或最优。
3. **修代码、修合同、修场景还是训练？** 本轮已修正消息账本观测缺陷，并通过相关回归；没有证据支持放宽版本、ACK、lease 或隐藏信息门禁，也没有证据支持偷偷降低故障强度/延长 deadline。当前首要缺陷属于策略未学会/策略动作利用不足，且需先解决单动作协议和紧时间预算的能力边界；只有在环境可行性范围重新冻结后，才可提出有停止条件的补训，不在本轮自动启动。
4. **哪些已有结果有效？** 原弱通信训练真实执行、checkpoint/优化器/日志、通信参数、世界模型预测负结果、B/C 公平对照、零越权和安全门禁结果仍有效，适用范围是原冻结合同与 tape。原“弱通信训练闭环完成”不能升级为“弱通信可用”。
5. **是否通过？** 弱通信可用性未通过。缺口是完整冻结任务规模上的正面服务/恢复率不足、当前 GPPO 在可见候选后的动作选择失败、尚无多任务可行性上界与单动作容量的正式边界报告；真实网络/控制周期也未验证。

返航、换电、充电、长期失联自主执行仍为待确认/未实现范围；真实飞行、生产认证和人工汇报活动没有被本轮替代或声称完成。

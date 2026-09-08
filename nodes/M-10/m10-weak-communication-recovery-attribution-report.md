# M-10 弱通信事件恢复失败归因

## 结论先行

本轮没有训练，也没有启动 B/C，未重跑整套课程。基于阶段二已经冻结的 `composite` validation tape，使用每个 seed 的 `new-step-16384.pt` 做确定性 episode-start 复放，并在策略分支首次合法收到故障遥测的决策边界做同状态只读分支。

主要结论是多因素共同造成，不能归为单一“信用分配”问题：

* 原恢复指标存在分母缺陷。旧实现仅在已经出现“另一 UAV 接管命令”时才计入分母，因此旧的 8/11/12 不是所有恢复机会的比例。
* 按修正口径，策略分支有 96 个事件—任务机会，完成恢复 1 个，即 1/96；参考调度器自己的分支有 84 个机会，完成恢复 0 个，即 0/84。
* 策略 96 个机会中：47 个没有形成完整公开合法候选（37 个必需任务遥测缺失/过期，10 个已无剩余 deadline/service）；19 个有候选但未选择；7 个在命令/ACK/资源门禁处失败；19 个接受后物理上已来不及，另有 1 个相关 lease 在 UAV 到达前过期，2 个恢复了部分服务但未在 deadline 前完成，1 个按定义完成恢复。
* 在策略分支状态的合法故障获知边界替换为参考调度器，4 个目标最终完成，但这 4 个在原策略分支也已完成，所以新增“挽救未完成事件”为 0；这不是参考调度器的额外救援收益。
* 弱通信可用性仍未通过。当前最小下一步不是扩训，而是修正恢复指标/机会定义并改善恢复机会的可观测性与场景课程；确认后再提出单假设、有预算上限的训练。

## 版本与保护检查

* 隔离工作区 `E:\Z博士\9.2日\GPPO-WORLD-9.2-lease-fix` 当前 HEAD：`3fd10e06c67cac708232d01ed60290309928d9e8`。
* 用户报告的远端提交：`09e4db7048ad0665b6c0a5155ff66cbd80ebdd6a`；本轮未 reset、未 force push、未修改 main 或历史 Release。
* 主工作树仍是独立的 `6da0a3ba8c6c4c22e271dc9f1e959d552b66be87`，保留其 staged/modified/untracked 文件；并发 commit 进程仅做只读确认，未终止、未删锁。
* 服务器使用专用诊断目录 `/home/user1/m10-runs/20260908-recovery-attribution-v1`；诊断完成后无 M-10 训练/诊断进程，GPU 空闲。未修改共享环境。

## 分母与原口径复核

阶段二原函数 `tools/run_m10_weak_course.py::recovery_pairs` 的实际条件是：先找出事件结束时受影响资源上的 travel/service 任务，再只有在 `execution_log` 中找到另一 UAV 的 accepted handoff 后才 append pair。这样把“没有产生接管命令”的失败机会排除，指标更接近“已发起接管后完成的比例”，不能命名为完整恢复率。

本轮修正口径：对每个分支，凡 `damage`/`disconnect` 事件在受影响资源上的实际 travel/service 区间于事件时刻结束，就按“事件—被中断任务”计一个机会；没有接管命令仍进入分母。事件没有中断任务时才不是恢复机会。多事件、多任务按独立事件—任务 pair 计数；未因策略失败事后删除。

| 分支 | seed-1101 | seed-2203 | seed-3307 | 合计 |
|---|---:|---:|---:|---:|
| 策略机会 | 32 | 30 | 34 | 96 |
| 策略完成恢复 | — | — | — | 1 |
| 参考调度器机会 | 28 | 28 | 28 | 84 |
| 参考调度器完成恢复 | — | — | — | 0 |

阶段二旧口径保持不变：策略为 1/8、0/11、3/12；参考为 0/11、0/11、0/11。它们仍可作为历史回归数字，但不再作为完整机会分母。

## 逐事件卡点汇总

以下分类来自逐步复放的公开快照、通信账本、执行 log、clock log、命令 task/UAV/version/token 和最终任务状态。`not_legally_informed` 在这 96 个已定义机会中为 0：故障遥测最终都被合法接收；但这不等于任务重分配所需字段及时、完整可用。

| 策略卡点 | 事件数 | 解释 |
|---|---:|---|
| 已获知但无完整公开合法候选 | 47 | 其中 37 个是任务必需字段 missing/stale，10 个已不再 pending、无剩余 service 或 deadline 已过 |
| 有具体候选但策略未选择 | 19 | 候选 action 明确包含目标 task 与可用 UAV，策略没有提交该 task 的接管 |
| 命令/ACK/资源门禁失败 | 7 | 例如 `command_lost` 或 `resource_busy`；安全门禁未关闭 |
| 接受后物理上已来不及 | 19 | 合法接管已接受，但从接受时 UAV 位置到 task 的最短移动+服务下界超过剩余 deadline |
| 接受后 lease/执行中断 | 1 | `cmd-00011` 于 t=10 接受，t=12 `lease_expired`，到达前未形成服务 |
| 服务恢复但未完成 | 2 | 已产生 post-event service，但 deadline 前不足以完成 |
| 完成恢复 | 1 | seed-3307 / `validation-mixed-seed-1011539`，damage `uav-2`，task-4；故障 t=7.4817，fault telemetry measured t=8、received t=9，另 UAV accepted t=10，completed t=14.1197，deadline t=14.4801 |

代表性失败卡：

1. seed-1101 / `validation-mixed-seed-1011506`：damage `uav-3`、task-3，event t=7.3907；故障 measured t=8、received t=9；t=9 的公开候选有 4 个，但策略未选择 task-3，最终 deadline t=11.5903 过期。
2. seed-1101 / `validation-mixed-seed-1011520`：damage `uav-2`、task-4，event t=8.4869；fault measured t=9、received t=10；`cmd-00011` 在 t=10 被 uav-3 接受，但 t=12 `lease_expired`，travel 尚未结束，未发生服务；后续 t=14 接受已经没有有效窗口。
3. seed-1101 / `validation-mixed-seed-1011502`：disconnect `uav-0`、task-0，event t=4.3880；fault measured t=5、received t=7；故障获知时 task-0 所需字段仍不完整/过期，deadline t=7.0177，未形成合法候选。

这些卡点分别覆盖了获知、公开 mask、具体选择、命令/ACK、lease 和 deadline；任何单一类别都不足以解释全部失败。

## 固定状态参考接管

策略复放在首次合法收到对应 `alive=0` 或 `connected=0` 故障遥测后的决策边界深拷贝环境状态；参考分支只使用该时刻已有 public view、mask、当前 ACK-confirmed continuation 和之后的语义地址化通信 tape，仍经过相同 command/ACK/version/lease/fencing/energy gate。策略和参考的完整 episode-start 前缀公开状态不相等，因此没有把普通 A/B episode-start 结果伪称为同状态因果比较。

固定状态分支中参考调度器完成的 4 个 task 都已在策略原分支完成；对策略未完成 task 的额外救援为 0。该结果不能证明参考调度器总体最优，也不能证明任何训练收益；它只说明在当前记录和事件边界上，没有观察到规则替换能额外挽救策略失败任务。

## 奖励、样本与训练决策

本轮使用已有轨迹的真实 return、task final state、clock service 和执行结果；没有重新训练，没有改变奖励，没有增加 NOOP 惩罚，没有把真值注入策略。

阶段一的三 seed 通过基础单任务/并行任务学习门槛，说明基本分配链和并行 lease 在小课程中可学习；不等于阶段二有足够的“故障发生—合法获知—接管—恢复”正样本。阶段二当前 3 seed 的修正机会数为 32/30/34，按完成恢复仅 1 个正样本；在旧口径中 8/11/12 的分母本身已选择性排除未发起接管的机会。现有证据支持“恢复学习样本稀疏且公开候选常被通信延迟/过期阻断”，不支持直接判断应加奖励项或无限扩训。

下一步最小假设：先冻结不含最终测试的恢复机会课程，使每个 seed 获得可审计的、公开信息可恢复的事件—任务机会与合法接管正例；然后在相同 reward/safety contract 下做有上限的 A-only 学习能力实验。只有该实验显示“公开候选已存在而策略仍稳定不选”时，才讨论恢复信用分配；若候选仍无法形成，应先修输入/确认合同或 tape，而不是补训。

## 测试覆盖审计：171 与 145 的差异

隔离快照收集 145 项的原因是：相对主工作树 171 项，缺少下列 31 个旧测试文件中的测试；隔离快照新增 5 个并行 lease 测试，所以 `171 - 31 + 5 = 145`。本轮新增 5 个归因测试后，在独立 basetemp 下本地全套为 **150 passed in 13.83s**；此前共享临时目录权限阻塞的 143 passed/7 setup errors 作为环境证据保留。这不是把测试数量当作能力证明。

缺失测试及能力状态如下；“部分”等效表示有相邻测试但不是原测试的同一断言。

| 缺失测试 | 源码能力仍在 | 当前等效/覆盖 | 缺失原因 |
|---|---|---|---|
| `test_future_tasks_do_not_change_initial_public_snapshot` | 是，`M10Environment`/`TaskPolicyView` | `tests/test_contracts.py` future evidence；非同一环境断言 | 隔离快照分支差异 |
| `test_assignment_requires_ack_and_then_accumulates_real_service` | 是，`TaskDecisionBridge`/`TaskExecution`/`ServiceClock` | `test_m10_parallel_lease` ACK 后 service；部分 | 旧环境测试未移植 |
| `test_damage_disconnect_and_energy_are_execution_events_not_policy_truth` | 是，事件只在 clock/executor 生效 | parallel fault + weak communication gate；部分 | 旧环境测试未移植 |
| `test_delayed_telemetry_is_not_visible_before_delivery_and_becomes_stale_by_age` | 是，`Telemetry`/view age | `test_m10_weak_communication.py` delay/expired | 由新弱通信测试覆盖等效语义 |
| `test_travel_then_service_then_idle_charges_actual_modes` | 是，`ServiceClock` | parallel service/energy；非完整模式断言 | 旧 motion 测试未移植 |
| `test_energy_exhaustion_in_transit_never_services_task` | 是 | 无同名等效，当前归因读取 clock 证据 | 缺少直接回归 |
| `test_damage_midflight_stops_motion_and_energy_consumption` | 是 | parallel fault only; 部分 | 旧 motion 测试未移植 |
| `test_deadline_before_arrival_expires_without_service` | 是 | stage2 deadline 统计；非直接单元断言 | 旧 motion 测试未移植 |
| `test_disconnection_cancels_transit_and_charges_idle_afterward` | 是 | parallel fault interrupts lease；部分 | 旧 motion 测试未移植 |
| `test_idle_exhaustion_without_task_assignment` | 是 | 无直接等效 | 旧 motion 测试未移植 |
| `test_partitioning_time_does_not_change_physical_result` | 是 | 无直接等效 | 旧 motion 测试未移植 |
| `test_assignment_does_not_complete_task` | 是，`TaskLifecycle` | parallel lease completion boundary；部分 | 旧 lifecycle 测试未移植 |
| `test_failure_preserves_work_and_requires_reassignment` | 是，`interrupt` 保留 service | parallel fault handoff；部分 | 旧 lifecycle 测试未移植 |
| `test_deadline_clips_service_and_does_not_complete_expired_task` | 是 | 归因 clock/final state；部分 | 旧 lifecycle 测试未移植 |
| `test_completion_exactly_at_deadline_is_valid` | 是 | 无直接等效 | 旧 lifecycle 测试未移植 |
| `test_hidden_task_cannot_be_assigned_before_arrival` | 是，view mask | weak delayed telemetry + contracts；部分 | 旧 lifecycle 测试未移植 |
| `test_overlapping_service_intervals_are_rejected` | 是，`ServiceClock` | parallel resource gate；部分 | 旧 lifecycle 测试未移植 |
| `test_invalid_rates_rejected` | 是，clock validation | 无直接等效 | 旧 lifecycle 测试未移植 |
| `test_future_task_does_not_allocate_slot_change_version_or_mask` | 是，slot/version contract | `test_m10_r2_correctness` + weak view tests；部分 | 旧 policy-view 测试未移植 |
| `test_hidden_truth_cannot_enter_via_unknown_field` | 是，whitelist | contracts future/no-future；部分 | 旧 policy-view 测试未移植 |
| `test_stale_data_retains_value_but_masks_proposal` | 是，view age/mask | weak overdue telemetry | 等效新测试已覆盖主要路径 |
| `test_duplicate_delivery_does_not_create_new_version` | 是，sequence/version | weak duplicate/stale audit；部分 | 旧 policy-view 测试未移植 |
| `test_received_energy_changes_mask_only_after_delivery` | 是 | weak delay mask test；部分 | 旧 policy-view 测试未移植 |
| `test_fixed_action_slots_resolve_only_delivered_ids` | 是，`resolve` | action identity tests in graph/weak paths；部分 | 旧 policy-view 测试未移植 |
| `test_undelivered_different_futures_have_identical_visible_state` | 是，received-only view | contracts no-future；部分 | 旧 telemetry 测试未移植 |
| `test_out_of_order_delivery_does_not_replace_newer_measurement` | 是 | `test_m10_weak_communication` reorder | 等效新测试已覆盖 |
| `test_stale_telemetry_keeps_value_but_marks_invalid` | 是 | weak overdue telemetry | 等效新测试已覆盖 |
| `test_conflicting_duplicate_rejected` | 是，Telemetry store | weak duplicate delivery audit；部分 | 旧 telemetry 测试未移植 |

因此本轮新增加的 5 个测试只验证归因工具的分母、延迟故障知识、候选未选择、无候选和通信分类；没有为了凑回 171 而复制 31 个测试。必要的并行 lease/continuation 能力由现有 `tests/test_m10_parallel_lease.py` 5 项覆盖，GAE、历史状态、触发、消息账本、候选身份和因果修正由隔离快照现有测试覆盖。若后续进入正式弱通信恢复研究，建议单独移植上述缺失的 motion/lifecycle direct regressions，而不是把它们的缺失隐藏在 150 的总数中。

## 产物与复现

只读诊断入口：`tools/diagnose_m10_recovery_attribution.py`。

本地复现（不读取 final test，不训练）：

```text
python tools/diagnose_m10_recovery_attribution.py \
  --phase2-root server-bounded-course-phase2-v1-download2 \
  --output m10-recovery-attribution-v6.json \
  --max-episodes 64 --device cpu
```

服务器复现目录：`/home/user1/m10-runs/20260908-recovery-attribution-v1`；输入为已存在的阶段二输出，输出为 `output/recovery-attribution-v4.json`。最终服务器文件下载到本地 `m10-recovery-attribution-server-v4.json`，服务器与下载文件 SHA-256 均为 `ffcddd44d5ac4c6d09845e28b32b92814f2ec836facc19528adaf2f9b8d1eb1f`。

诊断 JSON 包含：三 seed 的 checkpoint/tape provenance、96/84 分支事件卡、每步 public snapshot/candidate/action、offline-only truth marker、command/ACK/lease/execution/clock/telemetry ledger、episode-start 分支比较和固定状态参考接管摘要。offline truth 只用于归因，不进入 actor 或调度器。

## 状态与下一步

* 仿真研发/阶段二训练交付：已执行并保留；本轮归因：已完成。
* 恢复可用性：未通过；修正分母后为 1/96（策略分支完成恢复），参考分支 0/84。
* 稳定算法收益：未证明；三 seed、有限 validation tape 只支持有限结论。
* B/C：未启动，不能从本轮推断。
* 真实部署/控制周期：未验证。
* 返航/换电/充电：范围待用户确认，未在本轮暗中加入或排除。
* 人工群发、彩排、导师评审：未举行，待用户执行。
* `full_goal_complete=false`：恢复可用性未通过、必要范围和真实控制周期未确认，且 B/C 未启动。

**决策：本轮停止新增训练。** 先修正恢复指标与覆盖缺口，之后仅在用户确认研究假设后，提出一个有明确机会数、预算上限、成功门槛和失败停止条件的 A-only 恢复课程实验。

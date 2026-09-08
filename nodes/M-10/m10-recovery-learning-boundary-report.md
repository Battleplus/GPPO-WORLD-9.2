# M-10 恢复学习边界集与有界 A-only 协议冻结

日期：2026-09-08  
范围：只做边界机会审计、事件级口径修正和协议冻结；本轮没有训练，没有启动 B/C，没有重跑完整课程，也没有修改历史压力 tape。

## 结论先行

旧的“32/32 成功”不能继续表述为 32 个恢复事件成功。严格定义为：故障确实中断任务；控制端通过合法公开消息获知；获知后接受替代 UAV 命令；该替代 UAV 在故障后产生真实服务；任务在 deadline 前完成且安全拒绝为零。按此定义，原 selected 32 条只有 26 条满足，6 条的替代命令发生在合法获知前或获知后没有公开候选。旧归档原始结果保留，本报告只是限定其适用范围。

服务器权威复评在完整 256 条候选池上得到四类结果：参考/旧策略均成功 172，参考成功而旧策略失败 26，旧策略成功而参考失败 5，两者失败 53。26 条参考成功/旧失败中，只有 8 条旧策略自身确实经历了受影响任务中断；其余 18 条旧策略没有让受影响 UAV 承担该任务，不能作为恢复动作学习失败。8 条中没有一条同时满足“旧策略已合法获知且公开候选存在但未恢复”，所以当前开发集不能证明需要用 PPO 学习一个具体的恢复选择/时机行为。

因此本轮决策是：**不启动 A-only 补训**。冻结一个“有条件、未授权启动”的协议草案，只有后续独立开发集出现预先规定数量的候选可见而策略失败事件时才可开启；不会把当前 26 条原始四分类差异包装成训练收益证据。

## 版本与证据保护

- 本轮起始远端分支为 `c653d669a81e5d331300d4bfe8a5cfae373741f4`；本轮提交依次为 `932b9bb4d1511888864cf32a500fbaeaba7da761`、最终元数据提交 `a36f664f290909ce256f9d2cc38cfbcb6c23c1aa`。历史 `m10-recovery-observability-v1-20260908` tag 仍指向 `74078b53e4b566ad08780d79221b93f6e83373bf`。
- 隔离工作区本地 HEAD 为 `3fd10e06c67cac708232d01ed60290309928d9e8`；主工作树的 staged/修改/未跟踪文件、并发提交记录均未触碰。
- 旧 M-09/M-10/M-10-R/R2/R3、弱通信、归因、可观测性和有界课程 Release、checkpoint、失败记录保持原样。
- 本轮本地测试最终为 `158 passed in 9.32s`（隔离 basetemp），边界针对性测试为 `13 passed`；服务器专用环境针对性测试为 `4 passed`。
- 服务器专用目录：`/home/user1/m10-runs/20260908-recovery-boundary-v3`。复评结束无训练进程，GPU `0%`、显存约 `6/20 MiB`。

## 32 条 selected 的事件级复核

原筛选条件来自旧可观测性工具，允许“故障后服务”但没有强制替代命令必须在合法获知之后。因此新审计使用以下严格状态链：

`fault_time → legal_event_knowledge → public_candidate → alternate_accept → post_fault_alternate_service → deadline_completion`。

服务器结果按 split：

| split | 原 selected | 严格恢复服务/完成 | 说明 |
|---|---:|---:|---|
| train | 8 | 7 | 1 条获知后无公开候选 |
| validation | 8 | 6 | 2 条获知后无公开候选 |
| test（历史已查看） | 8 | 6 | 2 条获知后无公开候选 |
| OOD（历史已查看） | 8 | 7 | 1 条获知后无公开候选 |
| 合计 | 32 | 26 | 6 条不能计为事件恢复 |

32 条均由单任务场景生成，故障时确有受影响资源的 travel/service 日志；但“任务最后 completed”不自动等于“恢复”。严格成功记录要求 alternate command 的 accepted 时间不早于合法获知时间，并且服务日志资源必须是该 accepted alternate。没有空分母、故障前完成或无受影响任务被计入严格成功。

合法获知不只认 UAV 的 `alive/connected` 位：新鲜的 task `pending` 或 `remaining_service` 消息如果在故障后送达，也属于任务释放/可接管的公开证据；静态字段和隐藏真值不算获知。这样避免把已经通过合法任务公告获知的接管错误归为“尚未获知”。

## 完整候选池和选择审计

每个 split 原池 64 条（recovery 32、composite 32）。历史 selected 32 是旧可观测性工具按旧 `eligible` 条件取前 4 条/profile；本轮保留这批历史选择并逐条复核，同时按新严格定义另算“strict reference selected”候选。新候选按 profile、语义 seed 顺序取前 4 条严格参考成功，旧策略结果不参与选择。未选条目及失败原因保存在 `recovery-boundary-audit.json`，不是只保留容易成功的 32 条。

服务器完整池四分类：

| split | 两者成功 | 参考成功/旧失败 | 旧成功/参考失败 | 两者失败 |
|---|---:|---:|---:|---:|
| train | 44 | 7 | 1 | 12 |
| validation | 39 | 9 | 1 | 15 |
| test（历史已查看） | 40 | 6 | 0 | 18 |
| OOD（历史已查看） | 49 | 4 | 3 | 8 |
| 合计 | 172 | 26 | 5 | 53 |

26 条参考成功/旧失败跨越 14 damage、12 disconnect；参考获知后的 deadline slack 范围约 6.52–11.69 秒。进一步按旧策略自身状态复核：8 条是旧策略确实被中断，18 条是旧策略没有承担目标任务；在 8 条中，0 条出现“旧策略已有公开合法候选但未选择”。因此数量足以证明 selected 子集有性能上限/口径问题，但不足以证明“恢复动作选择学习”这个单一假设。

边界扫描共 34 条开发场景，覆盖：telemetry delay/max-age、disconnect duration、获知后 deadline slack、距离/服务量和并行任务竞争。服务器结果为：27 两者成功、6 两者失败、1 旧成功/参考失败、0 参考成功/旧失败。该扫描说明 slack 和 freshness 能把参考路径推入失败区，也说明当前小扫描没有制造出候选可见而旧策略选择失败的证据；它不是原压力分布总体性能估计。

## 数据用途和盲测边界

- 阶段二训练恢复样本数仍为 **未知**：已有 per-seed 制品是 checkpoint validation episode 导出，没有训练 rollout/event ledger；不能用 96 个 validation opportunity 冒充训练正负样本。
- 原 validation、旧 test/OOD、selected 32 和本次 full-pool 旧策略复评都已查看或用于决策；它们只能作为开发/历史回归，不能再称下一轮未见盲测。
- 新的最终测试须在训练起点、预算、课程和 checkpoint 选择规则冻结后，使用新的 semantic tape ID/seed 生成；不能按待评估策略失败逐条筛选。可另外生成“参考成功条件分布”与未经筛选的压力集，两者分开报告。
- 建议的未见集合命名为 `recovery-boundary-final-test-v1`，独立于现有 `recovery-opportunity-*` seed；最终输出在训练与验证选择完成前封存，不读取其结果。

## A-only 协议草案（当前不启动）

由于“候选可见而旧策略失败”当前为 0，本协议只是有界重启条件，不是本轮训练授权：

1. 预条件：新开发集必须在不使用最终测试、不暴露真值、不放宽 mask/ACK/lease/fencing 的情况下，出现预先规定的候选可见失败；至少覆盖 damage 和 disconnect，并且失败不主要由合法获知缺失或 deadline 必然不足造成。未达到则停止，不训练。
2. 起点：三个 seed `1101/2203/3307` 各自使用阶段一 `step-8192.pt`；旧 checkpoint 另列为不训练参考。
3. 两支路：control 使用原弱通信课程；treatment 使用同一原课程预算，其中预先固定比例采样严格参考可恢复边界事件。两支路只改变课程采样，Graph-5、动作、NOOP、奖励、执行合同、optimizer 配置、seed 和评估 tape 全相同。
4. 预算：每支路每 seed 最多 8192 环境步，每 2048 步保存/验证；两支路合计最多 49152 环境步。全程墙钟上限暂冻结为 4 小时；若启动前 pilot 的实测吞吐推算超限，先报告冲突，不静默缩水或超额运行。
5. 选择与停止：验证只使用冻结 validation；不看最终 test 选 checkpoint。非有限损失、任何重复/越权/ACK 身份/fencing 错误、事件 ledger 缺失或数据泄漏立即停止该支路。若到 8192 步候选可见恢复率没有达到预先写入的门槛，停止，不追加预算。
6. 必备 ledger：训练 rollout 逐事件保存 fault time、affected task、legal knowledge、candidate set、action、command、ACK、lease、service、completion、deadline、通信 message ID/状态；只保存公开输入给策略，真值只作事后审计。
7. 指标：候选可见恢复服务率、deadline 前恢复完成率、获知→接管、接管→服务恢复、未恢复数、基础分配保持率、安全错误、actor/continuation/optimizer 次数和计算成本。按训练 seed、tape split 和条件分布分别汇总。

在当前证据下，协议第 1 条未满足，故不启动。

## 归档

服务器最终 JSON：

- `recovery-boundary-audit.json` SHA-256 `fddf511dc182cc86c881779d060eb08a70e4e838816b415de60473b4df0793cd`
- `boundary-tapes.json` SHA-256 `d81a6c90abeff713689982b483c33ef4b7057275e8c39a07439637c592a0fc37`

本地下载后与服务器 SHA-256 一致。复现命令、逐条 full-pool 轨迹、strict selected tape、边界扫描、旧 checkpoint provenance 和服务器 pytest 输出随本轮独立诊断包保存；没有覆盖旧 Release。本轮不创建训练归档，不启动 B/C。

独立归档：[m10-recovery-learning-boundary-v1-20260908](https://github.com/Battleplus/GPPO-WORLD-9.2/releases/tag/m10-recovery-learning-boundary-v1-20260908)。最终 `final2` 资产在上传后按 GitHub API digest 复核；该 Release 只包含本轮审计和协议，不包含新训练。

## 状态

- 课程可行性：参考调度器在严格 selected 开发样本可形成合法服务路径，但原压力分布仍未通过。
- 合法获知：有真实 telemetry 路径；获知定义已扩展为 fault bit 或合法 task release 状态。
- 恢复服务：严格 selected 为 26/32；不是 32/32。
- 恢复完成：严格 26/32；完整池参考 198/256、服务器旧 checkpoint 176/256，均为开发复评，不是训练收益。
- A-only 补训：当前不具备可检验的候选可见失败条件，未启动。
- B/C：未启动。
- 真实部署、返航/换电/充电、实际控制周期和人工汇报：继续待确认/未验证。

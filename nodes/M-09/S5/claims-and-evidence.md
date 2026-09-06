# S5 外部声明与证据对照

类别含义：`completed` 为本轮有可复核证据的完成项；`history` 为历史冻结资产的复现/引用；`inference` 为基于证据的工程判断；`unverified` 为未验证、未声明。

| 声明 | 适用版本、模型、环境 | 证据位置 | 类别 | 限制与不扩张 |
|---|---|---|---|---|
| S1-R2 修复后的 60 条固定 tape 通过 | 三类型 GPPO，S1-R2 fixed baseline，server Python 3.10.12 / Torch 2.2.2+cu121 | `nodes/M-09/S1-R2/final-report.md`、`server-evidence.json`、`scenario-summary.json` | completed | 不是五类型实现；旧 S1/S1-R 结果保留为历史，不能混用 |
| 事件到达前配对输入/动作相等，到达后才可不同 | S1-R2 causal-pair fixture | `nodes/M-09/S1-R2/scenario-summary.json` | completed | 证明的是固定夹具中的可见时序，不是所有外生事件的预测能力 |
| 低置信度 0.55 会被消费且单源保持 SUSPECTED | S1-R2 payload/confirmation fixture | `nodes/M-09/S1-R2/scenario-summary.json`、`diagnostic-summary.json` | completed | 两源确认另有独立 fixture；不等于策略学会了置信度语义 |
| S2 `inference_mode` 低风险优化有效 | T-05 三类型 GPPO，seed 1101 / step 50000，6 类×10 tape，CPU 与 `cuda:0`，5 次交错重复 | `nodes/M-09/S2/comparison.json`、`final-report.md` | completed | 只支持该硬件、负载、实现和测量协议；不推断 CPU/GPU 是算法效果 |
| CPU 端到端均值从 4.277103ms 到 4.150364ms | 同上；配对 tape-group CI 为 -0.135745 到 -0.114669ms | `nodes/M-09/S2/comparison.json` | completed | 相对变化为 -2.927%；无实时控制周期，不声称实时达标 |
| GPU 端到端均值从 5.673699ms 到 5.489172ms | 同上；配对 tape-group CI 为 -0.203170 到 -0.170122ms | `nodes/M-09/S2/comparison.json` | completed | 相对变化为 -3.290%；不等于 GPU 优于 CPU，也不是 3-4 倍 PPO 结论 |
| A 的只读 Shadow 不改变策略行为 | S4 A，纯 GPPO，S3 checkpoint，S1-R2 60 tapes；Shadow ON/OFF | `nodes/M-09/S4/shadow-equivalence.json`、`final-report.md`；全量 pair=60/equal=60/return diff=0 | completed | S4 Shadow 是 side-car；context published 但 served_valid=0，不能写成策略消费 latent |
| A 的安全边界为零写入 | 同上 | `nodes/M-09/S4/shadow-equivalence.json`、`fault-injection-results.json` | completed | 计数器证明的是被测接口边界，不能替代真实飞控系统认证 |
| B 历史 adapter 确实消费 context | EAWM-GPPO seed 1101 / step 50000，EAWM-hard seed20260903，T-04 calibration | `nodes/M-09/S4/adapter-consumption-report.md`；S5 新复现 `reproduction-results.json` | history / completed reproduction | B 不是 S3 pure GPPO，不是新增训练，也不是公平增益结论 |
| B 的 635/577/58/487 定义 | B 的 100 held-out tapes；635 decisions；577 valid Shadow；58 fallback；487 decisions `latent_adapter_used=true` | `nodes/M-09/S4/server-evidence.json`；S5 `server-evidence.json` 与服务器 `evaluation.json`/trace files | completed | 487 是逐 decision trace 中 diagnostics 标记的计数；577+58=635；未将 tape 数误当 decision 数 |
| B fallback 的原因包含高不确定度和 OOD | 同上 | `nodes/M-09/S4/server-evidence.json`；`evaluation.json` shadow counters | completed | 58=11 high uncertainty + 47 OOD；timeout/stale-before/stale-after 均为 0；OOD 为合成 feature-range shift |
| timeout 是 post-inference fail-closed gate | S4 `ShadowRuntime` fault fixture | `nodes/M-09/S4/protocol.md`、`fault-injection-results.json` | completed | 不是硬取消、不是有界线程返回时间保证；本次注入为 calibration timeout+1ms |
| synthetic OOD 分数 269.0106024867358 触发 zero context | T-04 calibration，合成节点特征整体平移 +3.0 | `nodes/M-09/S4/fault-injection-results.json` | completed | 只验证合成门禁；不宣称真实未见任务泛化，input feature matching 仍是校准假设 |
| Shadow 不读取未来、不给真实 actuator 发 action | A/S4 side-car contract | `nodes/M-09/S4/interface-contract.md`、`protocol.md`、audit totals | completed | A 的纯 GPPO 在政策上不消费 context；历史 B 的 adapter 也不绕过真实 action mask/version/ACK/lease/fencing |
| episode end、task completed、infeasible、timeout 的语义已分离 | 三类型环境定义 | `nodes/M-09/S0/task-and-event-definitions.md`、S1-R2 scenario summary | completed | 当前没有逐 Task deadline 字段；业务 deadline、执行拒绝、政策自主性不是同一指标 |
| 汇报准备材料已经生成并渲染检查 | S5 deck + PDF | `slides/汇报.pptx`、`slides/汇报.pdf`、`slides/render-check.json` | completed | 实际汇报/导师评审未举行；日期仍是 tentative |
| 当前不需要新增训练 | S3 necessity review | `nodes/M-09/S3/decision.json`、`final-report.md` | inference | 只表示当前交付目标不需要训练；不表示 GPPO-History、五类型公平研究已完成 |
| 五类型、GPPO-History、稳定世界模型增益已完成 | 任何当前版本 | 无 | unverified | 明确不声明；需要新源码/数据合同、公平 paired training、held-out 多 seed 和重新验收 |
| “慢 3-4 倍”、实时达标、CPU/GPU 算法优劣 | 任何当前版本 | 无满足条件的公平资产 | unverified | 不在汇报和 Release 中作为事实 |

## A/B 冻结关系

A 是默认行为基线和安全演示；B 是历史接入路径的可追溯复现。A 的 `context_consumed=false` 与 B 的 `latent_adapter_used=true` 必须在报告中分列。A 的 zero-context parity 是“禁用/无有效 context 时回到纯 GPPO 路径”，不是“世界模型提升了 GPPO”。

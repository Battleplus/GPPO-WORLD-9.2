# M-10-R：训练有效性与公平性修正审查报告

日期：2026-09-07（北京时间）  
范围：本报告记录一次修正后的训练与验收闭环，不等同于无人机集群会议研发目标的完整研究完成。

## 结论摘要

本轮修正了五类会影响会议结论的实证问题：seed 不改变场景、缺少 Graph-5 Base、五类型图使用均值/最大值占位、世界模型没有独立测试指标且 context head 未进入损失、以及把 context gating 触发次数称为重规划次数。修正后，任务 tape 按 train/validation/test/OOD 集合冻结并可序列化复现；策略动作使用显式 UAV–Task 候选关系和实体置换验收；世界模型以监督 context 目标训练并报告独立测试与 OOD 指标；策略矩阵使用同一新环境、动作协议、评估 tape、终点和三个 seed。

正式服务器运行 `20260907-r-corrected-matrix-v2` 已完成：6 变体 × 3 seed × 2048 steps，每组 8 次实际 PPO optimizer update，共 18 个策略 checkpoint。服务器源码包 SHA-256 为 `5cf6146834d45dfe397c5aa3965a38ba220f7a42a671ce52d17f2e85b523c447`，训练归档 SHA-256 为 `bd5d01b52c09b793eb352854822f16e5690748292205ebb501d394afbb91eb4b`。

结果没有证明世界模型或触发机制带来稳定收益。Graph-5 World 与 Graph-5 Triggered-Replan 在本协议的五个测试 tape 上均值相同；触发组的 217 次触发均来自 `public_event`，不是一次经过误触发/漏触发优化的生产重规划器。因此它只能报告为事件强制重规划对照，不能解释为已验证的模型触发优化。

## 实证缺陷、设计取舍与待验证项

### 已由代码和运行证据确认的实证修正

- `default_scenario(seed, split)` 对非回归 seed 生成不同任务位置、到达、deadline、服务量、优先级和事件 tape；`scenario_tape` 与 JSON round-trip 使划分可复现。seed 0 的固定回归场景保留。
- 五类型表示显式展开 UAV、Region、Target、Task、Event 节点；UAV–Task 边编码距离、可见性、动作合法性和 Region 关系。Graph-2 只压缩实体类型，不删除声明的公开观测；有损差异仍单列。
- actor 对每个 UAV–Task 候选计算 pair score，另有 NOOP score；交换任务实体后候选分数相应置换，因果验收通过。
- 世界模型预测 `[reward,event_0..3,done,time_fraction,event_signal]`，context head 进入训练损失。`world-model.json` 报告 frozen tape 的 train/validation/test/OOD 划分、测试指标和简单训练均值基线。
- context 输入对当前合法动作做均匀合法候选期望；显式非法动作被拒绝；非有限或极端 context 走零 context 安全回退。
- 触发控制器强制响应新 public delivery、风险超过验证集阈值、安全/非法上一动作，且最大等待间隔为 3；不触发时复用上一次合法动作；安全 mask 和执行门禁始终生效。
- `ServiceClock` 对近重合位置采用 `1e-12` 距离容差，避免浮点误差形成零时长移动边界；新增回归测试覆盖该故障。

### 明确的设计取舍

- 环境采用归一化仿真单位，4 UAV、6 task slots、18 时间单位、25 个动作、3 Region、4 Target；移动/服务/等待能耗、deadline、损毁、通信、ACK、版本和独占 lease 均在协议内。返航、换电和充电未暗中假设为已验收。
- 触发实验使用直接事件/风险门禁和上一合法动作复用，未把每个环境 step 都计作重规划；但是正式矩阵中 Graph-5 Base/History/World 每步仍按共同训练收集协议重算策略，`replans=256` 是每次 rollout 的重算记录，不应混同为触发次数。
- 世界模型预训练成本单列；策略仍从各自 seed 从头训练。旧 1024-step 结果和阈值 0.5 零触发/0.2 敏感性结果不改写，继续作为短预算/历史范围证据。

### 尚未闭合的研究问题

- 当前是归一化仿真，不是实际飞控、无线链路或竞赛控制周期测量；未知控制周期时不宣称实时达标。
- 只有三个训练 seed、2048 steps；这足以证明真实更新和公平协议执行，不足以给出稳定泛化或显著性结论。
- 返航/换电/充电最低验收范围、真实任务规模和汇报日期待用户确认。
- OOD 只有冻结的合成集合；异常、stale、timeout 的回退在组件/合成验收中验证，不扩大为生产保障。
- 需要更长预算、更多 seed、真实五类型任务资产、网络延迟/控制周期和导师实际评审后，才可形成完整会议结论。

## 正式矩阵（服务器）

下表为五个评估 tape 的每 seed 均值，再对三个训练 seed 求均值；括号为三个 seed 间样本标准差。完整逐 episode/逐 seed JSON 在训练归档中。

| 变体 | 完成数 | 过期数 | return | 剩余能量 | 实际更新 | 触发/评估 |
|---|---:|---:|---:|---:|---:|---:|
| MLP-2 Base | 4.20 (0.60) | 1.80 (0.60) | 33.822 (8.337) | 23.777 (0.875) | 8/seed | 0 |
| Graph-2 Base | 4.33 (0.50) | 1.67 (0.50) | 35.596 (7.029) | 22.614 (0.384) | 8/seed | 0 |
| Graph-5 Base | 3.80 (0.53) | 2.20 (0.53) | 28.184 (7.399) | 23.296 (0.144) | 8/seed | 0 |
| Graph-5 History | 3.60 (0.60) | 2.40 (0.60) | 25.408 (8.355) | 23.606 (0.560) | 8/seed | 0 |
| Graph-5 World | 4.00 (0.00) | 2.00 (0.00) | 30.981 (0.046) | 23.265 (0.580) | 8/seed | 0 |
| Graph-5 Triggered-Replan | 4.00 (0.00) | 2.00 (0.00) | 30.981 (0.046) | 23.265 (0.580) | 8/seed | 217 total，public_event |

三 seed 为 1101、2203、3307；评估 seed 为 4401–4405；所有评估记录 rejected 均为 0，但这不是生产安全保证。旧 M-10 的 5 变体 × 3 seed × 1024 结果保留在旧文件和旧 Release，不能与本表混合汇总。

## 世界模型与触发

世界模型 tape 共 64 train episodes、16 validation、16 test、16 OOD，transition 计数为 1084/268/272/270。测试集指标为：reward RMSE 3.632、event BCE 0.262、event accuracy 0.956、done BCE 0.267、done accuracy 0.941、context RMSE 1.303。简单训练均值基线为 reward RMSE 3.678、event BCE 0.168、done BCE 0.224；因此本轮指标不支持“世界模型全面优于简单基线”。OOD 指标为 reward RMSE 3.428、event BCE 0.263、event accuracy 0.956、done BCE 0.268、done accuracy 0.941、context RMSE 1.234，仅代表该冻结合成 OOD tape。

阈值由 validation rows 的 F1 在候选 `0.1..0.9` 中选择，选中 0.2；test 未参与校准、预处理或选择。0.5 零触发和 0.2 敏感性历史结果仍保留。正式触发组实际 217 次事件触发，所有已记录原因为 `public_event`；没有足够证据报告模型风险门的误触发/漏触发优化收益。

## 安全、延迟与验收

本地受控测试为 151 passed；Shadow 定向复核为 6 passed，历史两项 50 ms timeout 失败记录未删除，未放宽门槛或改写归因。服务器源码归档全套回归为 144 passed、7 skipped；skip 均是项目既有 pinned GPPO baseline 未提供。服务器因果验收 10/10，覆盖未来事件不可见、seed tape 差异、延迟消息、stale、ACK/lease、真实能量拒绝、事件调度、完成分类、候选置换和世界模型动作/OOD 回退。

完整决策链测量包含观测构建、world model、policy、门禁、必要同步及 environment step，100 samples：CPU mean/P95/P99 为 2.872/3.081/3.091 ms；CUDA mean/P95/P99 为 3.565/3.786/3.803 ms。环境 step 单独均值约 1.36 ms，不能代替完整链路。测量运行在服务器 2×RTX 2080 Ti、Torch 2.2.2+cu121 的归一化仿真上，未知真实控制周期，不宣称竞赛实时达标。

## 交付边界

本报告、`training-results-r-summary.json`、`world-model-training-r.json`、`causal-acceptance-r.json`、`server-evidence-r.json` 与 `m10-r-reproduction-runbook.md` 描述 M-10-R；旧 M-10 报告、旧 Release 和负结果保持原样。成功矩阵、先前失败尝试、源码、tape、checkpoint、optimizer/recovery state、日志和服务器测试均在独立训练归档中。GitHub 新 Release 只在这些材料提交并校验后创建，不覆盖 main、M-09 或旧 M-10 Release。

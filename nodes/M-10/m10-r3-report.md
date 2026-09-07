# M-10-R3：预测质量、触发成本与学习充分性评估

日期：2026-09-07。本文记录 R3 的独立评估，不改写 M-09、M-10、M-10-R 或 M-10-R2 的历史报告、Release、原始训练和负结果。

## 技术摘要

R3 得到三个结论。第一，固定 R2 世界模型在新 final-test tape 上只显示轻微 reward 误差改善，事件和 done 预测没有达到可以支撑模型触发的质量。第二，在同一 Graph-5 World 策略 checkpoint 上，阈值 0.1 的 model-risk 触发每一步都触发，因而与周期策略完全相同且承担世界模型成本；规则触发减少了 actor 调用，但任务效果明显下降。第三，8192 环境步的学习曲线仍在变化，正式 3-seed 公平矩阵显示 Graph-5 World 没有超过 MLP-2 或 Graph-2，因此没有证据支持继续无目标扩训。

R3 因此支持一个受限负结论：当前标签、事件密度、策略规模和触发协议下，每周期策略是更稳妥的仿真基线；若继续研究，应先重定义“未来需要重规划”的预测标签并扩大独立事件 tape，再做有约束的定向实验。R3 不证明生产安全、竞赛实时性、实飞效果或世界模型一般无效。

## 关键结果

### 1. 预测目标不是已验证的重规划标签

`collect_world_dataset` 的事件标签来自 `env.step` 后新增的 ServiceClock 事件，预测窗口是下一个环境决策间隔。四个事件位中，damage、disconnect、reconnect 分别表示该间隔内出现对应新事件，第四位在当前模拟器中恒为零；done 表示该步之后的 terminated 或 time-limit truncated。标签描述了模拟器后果，不等价于“下一步必须重规划”。普通遥测刷新也没有被写成事件标签。

新 final-test tape 是独立冻结的 16 个 episode、276 条 transition。三类事件各有 16 个阳性样本，阳性率约 5.8%；第四类没有阳性样本，不能用 PR-AUC 解释其能力。训练、validation、历史回归 test、OOD 和 final-test tape 使用不同 seed 地址；历史 test 只作回归，不再声称是新的盲测。

固定 R2 world-model checkpoint 在 final-test 上的结果如下：reward RMSE **3.046**，训练均值 reward baseline RMSE **3.099**；event BCE **0.258**，训练阳性率常数 baseline 的同指标为 **0.166**；done BCE **0.266**，训练阳性率常数 baseline 的同指标为 **0.221**，全零常数 baseline 的同指标为 **0.934**。此前记录的 done 全零 Brier **0.058** 只与 Brier 比较，不能和 BCE 直接比较。damage/disconnect/reconnect 的 PR-AUC 分别为 **0.077/0.134/0.061**，0.5 阈值 precision 和 recall 均为 0。校准使用 10-bin ECE；对应 ECE 为 **0.127/0.140/0.114**。这些数值说明 event head 没有提供可依赖的事件触发信号；done 的 BCE 相对全零基线改善，但未超过训练阳性率基线，不能把 risk 0.1 门槛当作经过性能约束选择的阈值。

训练均值、持久性和零事件规则均保存在 `prediction-audit-r3.json` 对应的 Release 制品中。持久性基线只重复最近一次公开 UAV 语义状态变化；它是适用的事件基线，不是对 done 的强行类比。所有基线、预处理和阈值选择只使用训练/validation 语义，final-test 在选择后才使用。

### 2. 同 checkpoint 触发对照没有显示触发收益

比较固定 R2 `graph-5-world/seed-1101.pt`、固定阈值 0.1、固定 16-episode final-test tape。周期策略、规则触发和 model-risk 触发不重新训练权重。规则触发只使用公共语义事件、安全门禁和最大等待；model-risk 在同一 snapshot 上一次计算 context/risk，语义、安全、等待和 risk 共用该结果，不重复推理。

| 触发方式 | return 均值 | 完成均值 | actor 调用/episode | continuation/episode | world 调用/episode | CPU mean/P95/P99 ms |
|---|---:|---:|---:|---:|---:|---:|
| 周期策略 | 19.500 | 3.188 | 16.188 | 0.000 | 16.188 | 2.226 / 2.361 / 2.407 |
| 公共事件+安全+最大等待 | 6.552 | 2.250 | 9.125 | 7.875 | 9.125 | 1.943 / 2.360 / 2.406 |
| 规则+模型 risk | 19.500 | 3.188 | 16.188 | 0.000 | 16.188 | 2.219 / 2.350 / 2.393 |

规则触发共 146 次 actor 调用，model-risk 共 259 次；model-risk 的 risk 条件逐步成立 259 次，说明阈值 0.1 仍然每步触发。规则触发节省约 43.6% actor 调用和世界模型调用，但同时 return 下降约 12.948、完成数下降约 0.938；这不是可接受的成本收益折中。CUDA 测量也保留：周期/model-risk mean/P95/P99 为 4.276/2.997/3.063 和 2.838/2.971/2.993 ms，规则为 2.344/2.976/3.026 ms。CUDA 首样本含预热后设备同步影响，所有原始 259/272 个样本均保留，P99 只作本服务器仿真描述，不宣称控制周期达标。

触发条件的独立计数保留在逐 episode 记录。规则组包括 initial 16、task_arrival 76、confirmed_fault 32、link_recovery 16、completion_or_invalidation 44、safety 7、max_wait 30；model-risk 另外记录 risk 259。多条件同时成立时仍按冻结优先级归因，独立计数不因归因清零而丢失。安全条件没有为了制造节省而关闭。

### 3. 8192 步仍有学习变化，但 World 没有公平收益

服务器阶梯先运行 Graph-5 Base、Graph-5 History、Graph-5 World，seed 1101，预算 2048/4096/8192 环境步。实际 optimizer steps 严格为 32/64/128，吞吐分别约 Base 74.0、History 68.4、World 70.3 env steps/s。validation return 从 2048 到 8192 的变化为：Base 30.963→29.251、History 25.756→35.421、World 25.641→37.128。这个结果足以拒绝“2048 已充分”的假设，但不足以证明 8192 收敛。

据此冻结 8192 环境步、3 个训练 seed（1101/2203/3307）和同一新 final-test tape，运行五组公平矩阵。每个 seed 都是 32 rollout、128 实际 optimizer steps、8192 actor decisions；世界模型预训练成本沿用 R2 checkpoint，单列而未混入策略更新。

| 变体 | return 均值±seed SD | 完成均值 | 过期均值 | 吞吐 env steps/s |
|---|---:|---:|---:|---:|
| MLP-2 Base | **32.445±1.785** | 4.104 | 1.896 | 142.9 |
| Graph-2 Base | **32.424±1.777** | 4.104 | 1.896 | 78.0 |
| Graph-5 Base | 29.521±2.523 | 3.896 | 2.104 | 77.9 |
| Graph-5 History | 30.988±1.884 | 4.000 | 2.000 | 68.4 |
| Graph-5 World | 32.156±2.179 | 4.083 | 1.917 | 70.6 |

三 seed 只能提供描述性不确定性，不能当作显著性检验。World 与 MLP-2、Graph-2 的差异落在相近的 seed 波动内；当前没有策略收益证据。各组拒绝数、能耗、逐 episode 任务状态和原始更新曲线均在正式矩阵制品中保存，不能只选最佳 seed 或 checkpoint。

## 协议、代码和测量定义

R3 新增 `evaluate_world_model_rows`，按事件类别输出 precision、recall、PR-AUC、Brier、ECE、阳性数、样本数，并报告 reward/done 误差及训练均值、持久性、零事件/永不 done 基线。`collect_world_dataset` 保存标签语义、tape_id 和持久性基线，避免在 split 后重新推断。

R3 新增 `_policy_input_bundle`。它在同一 observation/version 上返回门控向量、risk、完整 context 和完整向量；collect、evaluate 和 benchmark 的决策路径不再先算 risk 再用 `force_context` 二次调用 world model。R2 世界模型的 `context_head` 与 reward/event/done head 共享 backbone，并通过 `context_mse` 监督损失获得梯度；R3 没有重新训练它，而是冻结并审计该 R2 checkpoint。策略确实消费其 context，但这不等于 event 目标已证明适合触发。continuation 复用控制器已有动作，只推进 value/history 和租约，不创建新的 TaskExecution 分配命令。策略、世界模型、触发判断、门禁、同步和环境推进都计入完整链路延迟。

训练和评估仍使用同一可见任务、mask、ACK、版本、lease、fencing 和安全合同。PPO 记账区分 environment steps、rollout updates、update epochs、optimizer updates、actor decisions 和 continuation。历史状态在 episode 边界清零，非终止 rollout 使用下一状态 bootstrap，真实 terminated 不 bootstrap。

## 限制和未闭合范围

- 事件标签是 one-step simulator event consequence，不是经过任务效果验证的未来重规划标签；应先建立真正的 horizon/event-to-replan 标注再研究模型触发。
- final-test tape 是本轮新冻结的合成 tape，不代表真实任务分布；OOD 仍是合成 energy-insufficient tape，不是生产保障。
- formal matrix 使用 3 个训练 seed、16 个评估 episode tape，结论是描述性，不是统计显著性结论；训练曲线仍可能未收敛。
- 世界模型 checkpoint 没有在 R3 重新训练；R3 主要评估 R2 模型的预测质量、成本和策略消费路径。context 是 R2 中经 `context_mse` 监督训练的 projection head，R3 将该已训练输出冻结后接入策略；R3 没有新增 context 预测目标。
- 端到端延迟来自指定服务器的 CPU/CUDA 与归一化仿真，样本量 259/272；真实控制周期、网络、返航、换电、充电和实飞范围仍待用户确认。
- 服务器旧 pinned GPPO baseline 仍缺失，7 个历史测试 skip 单列，不能冒充覆盖；R3 未改变共享环境。
- M-09、M-10、M-10-R、M-10-R2 的历史 Release、失败记录、阈值 0.5 零触发结果和阈值 0.2 敏感性结果保持不变。

## 下一项决策

基于 R3 证据，不值得继续无约束扩训 World 或触发策略。若会议需要继续投入，最小有价值路径是：先冻结并验证“未来需要重规划”的事件标签和可接受安全/任务约束，再用更长独立 tape 做一次标签质量与阈值成本实验；在此之前增加 PPO 步数不会解决当前 event head 与目标语义不匹配。返航、换电、充电最低范围、真实控制周期和汇报日期仍由用户确认；群发、彩排和导师实际评审不属于本轮已完成事项。

## 制品与复现

服务器运行标识：

- `20260907-r3-prediction-trigger-cost-v1/prediction-cuda`
- `20260907-r3-prediction-trigger-cost-v1/trigger-cuda`
- `20260907-r3-prediction-trigger-cost-v1/trigger-cpu-v2`
- `20260907-r3-prediction-trigger-cost-v1/learning-ladder-cuda`
- `20260907-r3-prediction-trigger-cost-v1/formal-matrix-cuda`

复现命令、环境、checkpoint、optimizer/recovery state、tape、逐 seed JSON、原始延迟样本和 SHA-256 清单见 `m10-r3-reproduction-runbook.md` 与独立 R3 Release。源码修正提交为本地 `b3a0b6d`，远端分支安全更新头为 `935ee5e4586cad79d2a72c4da864ce36a7f77893`。

# M-10-R2：PPO 与触发机制正确性验收报告

日期：2026-09-07（北京时间）  
范围：本报告记录 M-10-R2 的代码修正、服务器 pilot 和同预算公平矩阵；不等同于无人机集群会议研发目标的完整研究完成。

## 结论

本轮修正并验证了三个会直接影响训练解释的缺陷：

- GAE 现在区分真实 `terminated`、时间上限/rollout 边界 `truncated` 和 episode 起点；非终止边界 bootstrap 下一状态价值，真实终止不 bootstrap，历史 GRU 在 episode 起点清零。
- 续行间隔不再调用 actor 或重复提交分配命令。只有实际重规划点采样 actor；续行通过已 ACK 的同一任务租约经 `TaskExecution.renew` 延长，critic 仍对所有环境步训练，actor PPO 损失只使用真实策略决策点。
- 普通遥测不再产生事件触发。任务首次可见、确认故障、链路恢复、完成/失效和安全门禁以独立布尔值记录；原因在修改等待计数前按固定优先级归因。

本地全套测试为 **160 passed**；服务器全套为 **153 passed、7 skipped**。skip 是服务器未提供项目既有 pinned GPPO baseline，已单列，不能当作全覆盖。新增 R2 测试 9 项通过。旧 Shadow 的两项 50 ms timeout 失败记录未删除、未放宽阈值，也未在本轮声称其性能原因。

## 实证缺陷与设计取舍

### 已修正的实证缺陷

1. 原 `_gae` 将 rollout 最后一条 transition 的下一状态价值固定为 0，混淆了时间截断和真实终止。`Transition` 现在携带 `terminated`、`truncated`、`next_value`；递归只跨非边界 transition，delta 对真实终止使用零 bootstrap。
2. 原 `forced_action=last_action` 仍先执行 actor 前向和分布采样，且环境仍提交一次新分配。现在 continuation 使用 `value_only`，环境不增加 command id、不调用 bridge proposal，只续同一 ACK lease；执行反馈记录为 `reuse_existing`。
3. 原 `event_signal` 由当前时刻收到的任何消息构成，周期遥测会被当作事件。现在只由语义事件旗标构成，消息接收仍受延迟、版本和可见性约束。
4. benchmark 原先始终测 actor 且只测 world 代表组；现测量观测构建、世界模型、触发门禁、actor 或 critic、必要同步和环境 step，并同时测 world 与 triggered 代表组。
5. 训练元数据现在分别报告 `environment_steps`、`rollout_updates`、`update_epochs`、实际 `optimizer_updates`、`actor_decisions` 和 `continuation_steps`，不再把 rollout 次数冒充 optimizer 更新次数。

### 冻结的设计

- 仍采用 4 UAV、6 task slots、25 个动作（UAV–Task 候选加 NOOP）、18 个归一化时间单位、任务到达/服务/deadline/能耗/损毁/通信/ACK/版本/lease 语义。返航、换电、充电、真实控制周期和真实飞行物理未被静默纳入。
- 触发优先级固定为：`initial > safety > confirmed_fault > link_recovery > task_arrival > completion_or_invalidation > risk > max_wait`。不触发时执行已 ACK 任务的 continuation；安全门禁仍可强制重规划。
- actor PPO 只对实际 actor 决策点计算 old/new log probability、ratio、policy loss 和 entropy；critic 使用全部 transition 的回报目标。世界模型预测风险的计算成本单列，不被误写成 actor 成本。

## 服务器 pilot

运行标识：`20260907-r2-correctness-v1/pilot-v3`。服务器专用环境为 `/home/user1/m10-test-venv`，GPU 为 2× RTX 2080 Ti；运行前显存空闲，既有 TensorBoard 进程保持不变。

pilot 使用 5 变体、1 seed、128 环境步、8 world episodes、5 world epochs，仅用于正确性、吞吐和路径验证。triggered 组得到 109 次 actor 决策、19 次 continuation；触发原因包含 `completion_or_invalidation`、`confirmed_fault`、`initial`、`link_recovery`、`risk`、`safety`、`task_arrival` 和 `none`，证明它不是“每步触发”或“任意消息触发”。pilot 触发阈值为 0.45。

完整链路 benchmark（100 samples）如下；`world_model_calls` 是世界模型推理次数，actor 次数只计实际 actor head 调用：

| 变体 | 设备 | actor calls | continuation | world calls | chain mean / P95 / P99 ms |
|---|---|---:|---:|---:|---:|
| Graph-5 World | CPU | 100 | 0 | 100 | 2.802 / 3.052 / 3.588 |
| Graph-5 World | CUDA | 100 | 0 | 100 | 3.482 / 3.675 / 3.694 |
| Graph-5 Triggered | CPU | 48 | 52 | 148 | 2.682 / 3.176 / 3.194 |
| Graph-5 Triggered | CUDA | 48 | 52 | 148 | 3.373 / 4.161 / 4.172 |

这些是归一化仿真与当前服务器条件的测量，不是竞赛实时达标证明。

## 同预算正式公平矩阵

运行标识：`20260907-r2-correctness-v1/formal-v1`。6 变体 × 3 seed（1101、2203、3307）× 2048 环境步；所有组共用 train/validation/test/OOD tape、动作空间、环境、评估 tape、PPO 终点和 4 个 update epochs。每个 seed 均为 8 rollout、32 次实际 optimizer steps；世界模型预训练成本单列。旧 M-10/M-10-R 训练和 Release 未修改。

下表为 3 个训练 seed 的汇总均值，括号为 seed 间样本标准差；评估使用同一组 5 个 test tape：

| 变体 | 完成数 | 过期数 | return | 剩余能量 | actor/continuation（训练） |
|---|---:|---:|---:|---:|---:|
| MLP-2 Base | 4.20 (0.60) | 1.80 (0.60) | 33.768 (8.342) | 23.102 (0.834) | 2048 / 0 |
| Graph-2 Base | 4.20 (0.53) | 1.80 (0.53) | 33.744 (7.373) | 22.794 (0.650) | 2048 / 0 |
| Graph-5 Base | 3.80 (0.53) | 2.20 (0.53) | 28.175 (7.408) | 23.193 (0.053) | 2048 / 0 |
| Graph-5 History | 3.67 (0.50) | 2.33 (0.50) | 26.322 (7.018) | 23.363 (0.365) | 2048 / 0 |
| Graph-5 World | 4.13 (0.42) | 1.87 (0.42) | 32.845 (5.836) | 23.235 (0.538) | 2048 / 0 |
| Graph-5 Triggered-Replan | 4.13 (0.42) | 1.87 (0.42) | 32.845 (5.836) | 23.235 (0.538) | 2048 / 0 |

正式验证集校准阈值为 **0.1**。在该冻结协议下，triggered 的 risk 条件每步成立，故正式测试没有 continuation 节省，且与 Graph-5 World 的结果相同；这是负结果，不应写成触发优化已带来收益。pilot 的 0.45 敏感性只作为 pilot 证据，不能替代正式 validation-only 选择。

## 世界模型独立指标

正式 world model 使用 64 train、16 validation、16 test、16 OOD episode tapes；test 未用于训练、预处理校准或阈值选择。test 指标：reward RMSE **3.631**、event BCE **0.259**、event accuracy **0.956**、done BCE **0.268**、done accuracy **0.941**、context RMSE **1.314**。训练均值 baseline 的 reward RMSE **3.678**、event BCE **0.168**、done BCE **0.224**；因此不能宣称世界模型全面优于简单基线。OOD 指标仅代表冻结合成 OOD tape，不是生产保障。

## 安全、因果与延迟验收

R2 新增测试覆盖手算 GAE、终止/截断、历史隐藏状态边界、首次决策、普通遥测不触发、确认故障、风险、最大等待、安全、真正不触发、actor 调用次数、continuation 执行、租约续期及训练记账。原有未来输入、mask、版本、stale、ACK、lease、fencing、隐藏能量隔离、实体置换和世界模型回退测试全部保留。

服务器正式输出中所有记录 `rejected=0`，但这只描述该仿真 tape；不能扩大为生产安全保证。当前 benchmark 的完整链路包括观测构建、世界模型、触发门禁、策略/critic、同步和 environment step。正式 representative 结果为：

- Graph-5 World：CPU 2.777/2.976/3.004 ms，CUDA 3.528/3.707/3.719 ms（mean/P95/P99）。
- Graph-5 Triggered：CPU 3.082/3.335/3.402 ms，CUDA 4.032/4.226/4.252 ms（mean/P95/P99）。

真实控制周期未知，不能宣称竞赛实时达标。旧 Shadow timeout 仍按原阈值记录，未归因于机器负载。

## 制品与边界

源码提交链为本地 `eed34b3` 起点，经 `74bbb6e`、`24a0114`、`5423bc2`、`dc054d4`；当前远端分支提交为 `b73bcbc3ce78cdc17cc5e365fa259a45e309ec2e`。R2 源码包 SHA-256 为 `298cc57e9fc3f465eefea131027c92e64002446d1ea2ab1fa30b5e801b44dd67`。完整 formal 制品已下载并核验，核心文件 SHA-256：`matrix-results.json=23c41c7c2c5f36fe5beb60b8c7c9e1148e425aa1dc1475b97b827c3e4256b820`、`world-model.pt=1ee46bfad4bdfe717a7a1ddbaf0ef51c8a683c6184e84c33b9863f4b2563eb56`、`server-pytest.txt=5898a9d9da6a7e34246a0c3b73643af5fda44101d5ace46d40b634763949774d`。

旧 M-09、M-10 和 M-10-R Release、原始训练、失败记录和负结果保留不变；R2 使用独立 Release，不覆盖 main 或旧 Release。

仍未闭合：返航/换电/充电最低验收范围、真实任务规模、真实控制周期、更多 seed/更长预算、真实五类型任务资产、网络实测、实际飞行验收、群发/彩排/导师评审和最终汇报日期。故本报告不能作为完整会议目标完成声明。

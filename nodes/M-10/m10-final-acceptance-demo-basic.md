# 基础任务演示脚本（冻结候选）

用途：会议中演示基本任务分配、ACK、lease、deadline、能耗和安全拒绝。该脚本不训练、不选择测试集最优模型。

## 候选与依据

使用正式矩阵中 `MLP-2 Base / seed-1101` 的完整 checkpoint。它在既定 5 变体×3 seed×8192 environment steps 矩阵中有最高描述性平均 return 和吞吐；这是工程演示选择，不能称作无偏最优。周期决策是当前默认执行语义。

## 演示步骤

1. 展示最终复现 JSON 的 `protocol`、checkpoint SHA、源码 commit 和冻结 tape。
2. 运行 `normal`/`mixed` 轨迹，指出候选 action 的 UAV–Task 身份、公开 mask、policy version、command id、ACK 和 lease。
3. 展示 `uav_damage` 与 `communication_interrupt`：只在收到确认语义或安全门禁时改变决策；普通 telemetry refresh 不自动触发。
4. 展示 `energy_insufficient`：策略看不到隐藏真实能量，执行层可拒绝；拒绝不会绕过 `TaskExecution` 推进服务。
5. 以任务完成、expired、rejected、能量和完整链路延迟收尾。

复现入口：`tools/run_m10_final_repro.py --fusion base`。服务器命令、候选 checkpoint 路径和 SHA 见最终 artifact index；此处不放凭据。

## 讲解边界

这是服务时钟/消息/执行合同的仿真复现，不是实飞、生产认证或竞赛实时性证明。返航、换电、充电最低范围待用户确认。


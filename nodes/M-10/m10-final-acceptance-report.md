# M-10 会议交付总验收报告与候选冻结

日期：2026-09-07。依据：R3 已完成的预测、触发成本、学习充分性实验；本轮仅做证据总验收、材料收束和无训练候选复现。

## 结论摘要

基础任务分配和四类事件语义已在统一仿真环境中运行并通过既有因果/安全验收；R2 world model 已训练，R3 融合策略已训练并实际消费冻结 context；公平矩阵已执行，但在 3 seed、有限 tape 和 8192 environment steps 下没有稳定优势证据。模型风险触发当前每步触发，规则触发降低任务效果，因此周期决策冻结为当前可用默认。研发实验交付可以验收，算法稳定收益、真实部署和用户范围不能合并写成 passed。

## 证据核查

环境保持任务到达、真实服务进度、deadline、移动/等待/服务能耗、damage、通信中断/恢复、任务级 ACK、版本、fencing 和独占 lease。策略输入只来自实际收到的公开消息；隐藏真实能量可以导致执行拒绝，但不会直接改变策略特征或 mask。执行通过 `TaskExecution` 推进，诊断不绕过模拟反馈送达。

R3 final-test 预测审计为 276 rows、每类 damage/disconnect/reconnect 16 个阳性样本。reward RMSE 为 3.046，对训练均值 baseline 3.099 略好；event BCE 0.258 高于同指标训练阳性率 baseline 0.166；done BCE 0.266 高于同指标训练阳性率 baseline 0.221，低于全零 BCE 0.934。此前全零 Brier 0.058 只与 Brier 比较。event PR-AUC 0.077/0.134/0.061，0.5 阈值 precision/recall 全为 0。标签是下一环境决策间隔 simulator consequence，未证明是未来 replan 标签。

R3 正式矩阵为 MLP-2、Graph-2、Graph-5 Base、Graph-History-5 Base、Graph-5 World 各 3 seed、8192 environment steps、每 seed 128 optimizer updates、8192 actor decisions。return 均值依次为 32.445、32.424、29.521、30.988、32.156；这是配对 tape 上的描述性比较，不支持收敛、普遍无效或显著性结论。R3 复用了 R2 world-model 预训练成本，未重新训练 world model。

触发对照固定同一 Graph-5 World checkpoint 和 final-test tape：周期 return 19.500、actor 16.188/episode；规则 return 6.552、actor 9.125、continuation 7.875；model-risk threshold 0.1 return 19.500、actor 16.188、continuation 0，risk 259/259 步成立。规则节省调用但损害效果，模型风险不节省；安全强制条件未关闭。

## 候选与复现

默认候选：MLP-2 Base seed-1101。融合候选：Graph-5 World seed-1101 + R2 frozen world checkpoint。选择默认候选是工程演示选择，不是预注册无偏最优；融合候选只展示预测 context 消费和效果边界，不默认启用 model-risk。

最终服务器复现位于新目录 `20260907-final-acceptance-v1`，`training_performed=false`。基础轨迹为 5 个冻结语义场景、69 environment steps、69 actor calls、0 world calls、0 rejected；融合轨迹为 5 个场景、75 environment steps、75 actor calls、75 world calls、0 rejected。两份 JSON 包含 tape、逐步 mask/version/action、ACK/lease、事件、能耗、任务分类和终止语义。因 m10-test-venv 当前缺少 Torch/NumPy，未安装依赖；使用既有 s1-gppo-venv 只读运行，版本和偏差均留痕。

## 限制与未完成

- 仿真通过不等于真实飞行、生产认证、真实网络或竞赛实时达标；完整链路延迟是指定服务器归一化测量，真实控制周期未知。
- 返航、换电、充电是否属于最低验收，竞赛任务规模和控制周期待用户确认。
- 服务器旧 pinned GPPO baseline 缺失导致 7 项 skip，未冒充覆盖。
- 三因素复合扰动压力测试仅指当前 tape 中的 UAV damage、通信断开/恢复、低置信度观测/风险门禁条件；具体时序与持续时间以 tape 为准，不称生产攻击保障。
- 群发、彩排、导师评审未举行。

因此 `full_goal_complete=false`。本轮不值得无条件追加训练；若要继续，应由用户先确认范围或另立“未来 replan 标签/更大独立 tape”的有停止条件研究任务。


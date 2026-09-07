# M-10 会议研发阶段报告

日期：2026-09-07。本文只报告本轮在指定服务器真实运行的 M-10 仿真环境、训练和对照，不把 M-09 历史模型复现当作新训练结果。

## 结论

本轮完成了四类扰动的环境语义和第一版训练闭环：任务先到达再进入可见槽，策略只读已收到遥测，分配经过版本化提议和任务级 ACK，服务由 ServiceClock 按移动、服务、等待能耗推进。损毁会中断执行，断联会撤销可用执行链，能量不足会由执行层拒绝或中断，deadline 会区分完成和过期。

服务器完成 pilot 和正式矩阵。正式矩阵固定 4 UAV、6 任务槽、25 动作、18 时间单位、1024 steps/seed、seeds 1101/2203/3307，5 个变体各 3 seeds。MLP-PPO、Graph-PPO、Graph-PPO-History、world-context 和 event-triggered 均产生真实梯度更新并保存 checkpoint。

## 结果

| 变体 | 完成数均值 | 过期数均值 | return 均值 | 95% seed CI（return） |
|---|---:|---:|---:|---:|
| MLP-PPO / two-type | 4.000 | 2.000 | 31.071 | ±15.631 |
| Graph-PPO / two-type | 4.333 | 1.667 | 35.639 | ±9.138 |
| Graph-PPO-History / five-type | 4.333 | 1.667 | 35.685 | ±9.067 |
| Graph-PPO + world context | 4.000 | 2.000 | 31.000 | ±0.141 |
| Graph-PPO + event trigger | 4.000 | 2.000 | 30.956 | ±0.091 |

CI 使用三个 policy seed 的样本标准差，未把 5 个固定评估 episode 当成独立训练 seed。图策略在本预算下完成数高于 MLP，但 CI 很宽，不能宣称稳定算法收益。world context 与 event trigger 在此矩阵中没有提高完成数。阈值 0.5 的 event trigger 零触发结果被保留在 v1 归档，阈值 0.2 的结果作为敏感性补充，不能当作无偏阈值选择。

世界模型训练使用 1059 条 transition，episode-disjoint 划分为 train 732、validation 165、test 162。测试集没有参与训练、校准或选择。world model、策略 checkpoint、optimizer 状态和逐 seed 记录均在服务器归档中。

## 验收与时延

全环境因果验收 7/7：未来事件不改变初始公开快照，延迟消息在送达前不可见，stale snapshot 被拒绝，ACK 后租约推进并过期，隐藏执行真值可拒绝命令，损毁/断联/恢复事件按时调度，完成状态与过期状态分离。

服务器全套回归为 139 passed、7 skipped。跳过项是旧 GPPO baseline 不在专用环境中，不是本轮新测试失败。此前两个 Shadow 超时测试在服务器受控环境重跑均通过，原 50ms fixture 门槛没有改动。

代表性融合策略的服务器时延测量为：CPU policy mean 0.484ms、P95 0.499ms；GPU policy mean 0.950ms、P95 0.971ms。环境 step 与策略推理分开统计，不能把这组小规模仿真数字扩展为竞赛实时保证。

## 当前边界

返航、换电和充电动作尚未得到最低验收范围确认，因此本轮没有把它们伪装成 NOOP，也没有宣称已经支持。实际飞行动力学、通信网络传输、真实五类型资产、更多公平对照、生产 OOD、硬取消 timeout 和长期稳定收益仍未验证。人工彩排和导师汇报尚未发生，状态为 `not_held`。

## 归档

训练归档：`m10-training-artifacts-20260907-v2.tar.gz`，SHA-256 `8c883d7cc7213ed724dd86e2a99645f30e5a2fca084fc75df42ace5ea22d6312`。源码归档 SHA-256 `77321bb99bc400f238b7ad505c603f87267f9632ea810a319eee684eaa828ba6`。汇报稿已通过 10 页结构/字体/渲染复核：PPTX SHA-256 `02a1ce449359c80ac494a35f2ac5094430efab5e0a858763b7bc0ee119bd2b9d`，PDF SHA-256 `b6fd60af30c2c62e7f089ba8792bb351ee63270926b2986e9e24041ada6aa90c`。GitHub Release：[M-10 meeting research delivery](https://github.com/Battleplus/GPPO-WORLD-9.2/releases/tag/m10-meeting-research-v1-20260907) 已发布，Release API digest 与独立 CDN 下载的三项资产全部匹配。

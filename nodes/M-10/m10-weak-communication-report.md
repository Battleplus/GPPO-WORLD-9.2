# M-10 弱通信突发事件与 GPPO + 世界模型扩训报告

日期：2026-09-07。运行根目录：`/home/user1/m10-runs/20260907-weak-comm-v1`。本报告是新增阶段证据，不覆盖历史 Release、候选或负结果。

## 结论

弱通信协议已落地并通过本地 6 项新增测试、服务器 10 项直接合同审计。服务器 pilot 和正式训练均实际执行。三组都使用 Graph-5、同一环境/动作/奖励/门禁和冻结通信 tape：A 每周期 GPPO，B 同一 GPPO 加同一 world model 每周期输入，C 同一 world model 的事件触发策略。pilot 验证了真实梯度更新和吞吐；正式矩阵为 3 组 × 3 seed × 12,288 environment steps。

结果不支持宣称世界模型或模型触发带来稳定收益。正式 final-test 的组均值为：A return `-24.5201`（seed 间 SD `0.0637`）、完成 `0.0208`；B return `-23.9513`（SD `0.7408`）、完成 `0.0625`；C 与 B 相同。三组训练均为 12,288 环境步、12,288 actor decision、0 continuation、48 个 rollout 记录 × 4 epochs = 192 次实际 optimizer.step/seed。C 的阈值 `0.1` 是 validation-only 选择失败后的预设负结果回退；验证集没有同时满足任务效果不下降、安全门禁和 actor 调用减少的阈值。

## 预测与数据隔离

pilot world model 在 train/validation/test/OOD tape 上使用下一决策间隔的 reward/event/done/context 目标。其历史 final-test 指标为 reward RMSE `1.99665`、event BCE `0.28792`、done BCE `0.36961`；同一指标的训练阳性率基线为 reward RMSE `2.23626`、event BCE `0.16449`、done BCE `0.21932`。因此 reward 预测优于该均值基线，而事件和 done 预测较差；不能把 event accuracy（约 `0.957`）当作稀有事件有效性证据。模型没有凭空预测随机丢包具体时刻，标签只描述可由当前公开历史定义的 simulator consequence。`tapes.json` 保存 train 32、validation 16、historical_test 16、final_test 16、OOD 16 个独立 tape；历史 test 仅作回归，final test 未用于阈值/模型/预算选择。

## 成本与触发审计

对同一 final-test tape 和 seed-1101 checkpoint 的只读详细审计如下。延迟顺序为 mean/P95/P99，样本数均为 280 个端到端决策链样本，含观测构建、world model（若启用）、触发判断、actor 或 continuation、执行门禁、同步和环境推进；原始样本写入 `detailed-eval.json`。

| 对照 | return | 完成/过期/拒绝 | actor/continuation | world calls | latency ms |
|---|---:|---:|---:|---:|---:|
| A periodic | -24.475 | 0 / 6 / 0.938 | 17.5 / 0 | 0 | 4.081 / 2.885 / 2.941 |
| B periodic | -24.475 | 0 / 6 / 0.938 | 17.5 / 0 | 17.5 | 3.182 / 3.436 / 3.484 |
| B rules | -24.366 | 0 / 6 / 0.500 | 9.875 / 7.625 | 9.875 | 2.603 / 3.387 / 3.435 |
| C model-risk 0.1 | -24.475 | 0 / 6 / 0.938 | 17.5 / 0 | 17.5 | 3.112 / 3.400 / 3.448 |

C 的风险条件在所有决策步成立，未产生 actor 节省；B rules 少调用但任务效果没有改善，故不能作为默认触发方案。复合 tape 的 16 个 episode 共记录 12,570 telemetry sent、11,262 received、6,278 dropped；周期 A/B/C 的 command 为 265 sent、15 dropped，B rules 为 150 sent、8 dropped。审计 JSON 字节量是 canonical JSON 记录长度代理，不是实网字节测量；无自动 retransmission，计数为 0。无重复 accepted command、无 unauthorized/fenced execution；通信等待从 32 个 damage/disconnect 事件到首个合法相关 telemetry 平均 `2.214` 模拟秒，32/32 有配对；service recovery delay 为 null，因为这些策略在该 tape 未观察到恢复后的有效 service。

## 影响与边界

本阶段证明了弱通信 tape、三链路分离、消息可见性/过期/乱序/ACK/执行安全合同和实际扩训闭环；没有证明 B 优于 A，也没有证明 C 在保持任务效果和安全的前提下降低成本。当前建议保留周期决策作为可用工程演示，世界模型版本单独演示“预测输入实际被消费”；不启用 model-risk 触发。不要将当前 12,288 步、3 seed、有限合成 tape 解释为收敛、普遍无效或生产保障。

返航、换电、充电、长期失联自主执行不在本阶段动作范围，仍待用户确认；真实网络、实飞、生产认证、真实控制周期和竞赛实时达标未验证。人工群发、彩排和导师评审未举行。

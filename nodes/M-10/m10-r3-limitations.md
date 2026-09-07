# M-10-R3 限制、负结果与停止边界

- 当前世界模型事件目标是下一环境决策间隔内新出现的 ServiceClock damage、disconnect、reconnect 后果，不是已经证明的“未来需要重规划”标签。
- 三类事件在 final-test 各只有 16 个阳性样本，约 5.8%；第四事件位恒为零。必须报告 PR-AUC、precision、recall、Brier 和 ECE，不能用 accuracy 代替稀有事件质量。
- 固定 R2 world-model 在新 final-test 上 event PR-AUC 为 0.077/0.134/0.061，0.5 阈值三类 precision/recall 均为 0；event BCE 0.258 高于同指标训练阳性率基线 0.166。done BCE 0.266 高于训练阳性率基线 0.221，但低于全零常数基线 0.934；全零 Brier 0.058 不与 BCE 直接比较。R3 不宣称预测驱动触发有效。
- 阈值 0.1 在 model-risk 对照中每步触发，continuation 为 0；规则触发虽减少 actor/world 调用，但 return 从 19.500 降到 6.552，完成均值从 3.188 降到 2.250。
- R3 的规则与 model-risk 对照固定同一策略 checkpoint 和同一 final-test tape，但规则组在 continuation 不缓存跨版本 context，而是使用零 context 做 value/history 推进。这是明确的安全/一致性取舍，不是对生产部署的保证。
- 8192 步阶梯说明 2048 步不足以称学习充分，History/World 仍随预算变化；正式 3-seed 矩阵中 Graph-5 World return 32.156±2.179，没有超过 MLP-2 32.445±1.785 或 Graph-2 32.424±1.777。
- 正式矩阵每组每 seed 为 8192 environment steps、32 rollout、128 optimizer updates、8192 actor decisions。seed SD 只作描述性不确定性，不是显著性检验。
- 世界模型预训练成本沿用 R2 checkpoint，R3 未重新训练世界模型。R2 的 context head 与共享 backbone 通过 `context_mse` 监督损失训练，R3 冻结并验证了实际消费路径和推理成本；不能把 R3 说成重新训练了预测头。
- 延迟是指定服务器 CPU/CUDA 的归一化仿真测量，原始样本 259/272，真实控制周期和网络条件未知，不宣称竞赛实时达标。
- 服务器仍缺失旧 pinned GPPO baseline，7 个测试 skip 保留；不冒充全覆盖。
- 返航、换电、充电最低范围、真实控制周期和汇报日期待用户确认。R3 没有擅自排除，也没有把实飞/生产认证扩为本轮仿真必达。
- 结论边界：当前不值得无约束继续扩训。若继续，先重定义未来重规划标签并扩大独立 tape，再做有约束的阈值/成本实验。

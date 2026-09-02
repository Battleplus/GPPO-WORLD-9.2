# T-00～T-06 执行规划

## 总体依赖

```text
T-00 基线/合同
  └─ T-01 数据覆盖
       └─ T-02 基础图世界模型
            └─ T-03 自动事件 + GES
                 └─ T-04 Shadow/校准
                      └─ T-05 frozen latent + GPPO
                           └─ T-06 1～3 步想象
```

节点按门禁串行解锁；节点内部可并行开发，但不能越过前置验收。每个节点都必须更新独立节点页、`nodes/status.json` 和 checkpoint/evidence manifest。

## 阶段计划

| 节点 | 核心工作 | 关键产物 | 必须通过的 Gate |
|---|---|---|---|
| T-00 | 冻结 GPPO 基线、schema、字段注册表、因果白名单 | baseline/schema/feature registry manifest | 输入无未来信息；同一 recorder 服务 random/greedy/GPPO |
| T-01 | 采集覆盖性真实轨迹并严格切分 | dataset manifest、coverage report、split hashes | random legal/greedy/GPPO 与压力场景覆盖；split 无交叉 |
| T-02 | Graph encoder、action-conditioned dynamics、基础预测头 | base WM checkpoint、训练配置、一步/多步报告 | 可独立训练/保存/加载；优于朴素基线；action shuffle 退化 |
| T-03 | 自动事件生成、模态 event heads、GES | WM/EA-noGES/EAWM checkpoints 与消融 | event 指标优于频率基线，且基础预测不显著退化 |
| T-04 | 只读 shadow、校准、OOD 与延迟 | shadow logs、calibration/latency/safety report | belief/mask/version 零写入，回退 100%，风险门禁冻结 |
| T-05 | frozen latent adapter 接入 GPPO | 四组策略 checkpoint 与公平实验报告 | 可关闭、旧 checkpoint 兼容、非法动作/并发安全不退化 |
| T-06 | GPPO 候选动作的 1～3 步 imagined rollout | horizon 1/3/5 误差、合成比例/门控报告 | 收益出现在真实独立环境，不只在 predicted return |

## 执行优先级

### P0：T-00～T-02，先证明世界模型能正确学习动作后果

最小科学问题：相同历史、不同 executed action 是否产生可区分的下一图/reward/cost/continuation 预测？使用 action-shuffle 和 no-action 对照验证，避免模型只学时间相关性。

### P1：T-03～T-04，再证明事件感知有效且可信

分别比较 `WM`、`WM+Event(no GES)`、`WM+Event+GES`。事件指标必须按模态和稀有类别报告，不能仅报告 accuracy。Shadow 期不影响任何动作。

### P2：T-05，最后证明 latent 对 GPPO 有增量价值

冻结世界模型，保持动作空间、mask、奖励、训练预算、seed 和场景一致，只改变 latent 接入。首先验证 zero-context parity 和安全不变量。

### P3：T-06，可选研究

先 1 步、再 3 步；5 步只用于误差审计。按不确定度截断 rollout，限制 synthetic/real 比例。任何安全退化或独立测试无收益都回退到 T-05。

## 停止与回退条件

- 数据泄漏或 split 污染：作废受影响数据与其派生 checkpoint，回到 T-00/T-01。
- action-shuffle 不退化：说明动作条件未被模型使用，T-02 不得通过。
- event 头提升事件指标但拖垮基础预测：重新调节损失/GES，T-03 不得通过。
- 校准、OOD 或延迟不达标：保持 shadow，不进入策略。
- latent 接入导致非法动作、stale 提交或不可关闭：立即切回 no-WM GPPO。
- imagined rollout 只改善模型内 return：拒绝推广，保留 T-05 方案。

详细责任、证据和退出条件见各[节点页](../nodes/README.md)。

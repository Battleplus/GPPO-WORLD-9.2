# 范围、分工与安全边界

## 1. 总目标

构建动作条件、事件感知的异构图世界模型：

```text
(历史可见 belief 图, 实际执行动作, 已到达证据)
                         │
                         ▼
              Graph encoder + dynamics
                         │
                  latent [h_t, z_t]
       ┌──────────┬──────────┬──────────┬──────────┐
       ▼          ▼          ▼          ▼          ▼
  下一图/差分  自动事件   reward/cost continuation uncertainty
                         │
                         ▼
              可关闭的 frozen latent adapter
                         │
                         ▼
                       GPPO
                         │
                         ▼
       真实 mask/version/ACK/lease/fencing
```

## 2. GPPO 与世界模型的分工

| 责任 | GPPO | 世界模型 |
|---|---:|---:|
| 在候选动作中采样或选择动作 | 唯一负责 | 禁止 |
| 读取真实 action mask | 是 | 可作为观测/监督，但无写权限 |
| 预测执行动作后的状态与事件 | 否 | 负责 |
| 写入 belief、mask 或执行状态 | 由现有可信链路负责 | 禁止 |
| ACK、lease、fencing、版本校验 | 权威链路 | 禁止绕过 |
| 不确定时安全回退 | 原 GPPO 可独立运行 | 只发出 invalid/uncertain 信号 |

世界模型不会取代 GPPO。它是预测与表示学习模块；在线动作仍为：

```text
GPPO logits + 真实 action mask → 采样/argmax → 执行安全链路
```

## 3. 动作来源

- **特定的是动作合同**：UAV–Region 候选边和 NOOP 的语义由工程定义。
- **自主的是动作选择**：GPPO 在当前合法集合内选择具体动作。
- **世界模型看到的是 executed action**：训练记录必须使用经安全链路确认的实际动作，而非未执行的原始 proposal。
- **想象阶段仍不越权**：世界模型仅对 GPPO 提出的合法候选动作预测后果，不能自行向环境提交动作。

## 4. 事件感知与事件偏好

第一主线中的“事件”指 EAWM 式事件感知：从相邻可见观测自动生成 ordinal、nominal、structural、evidence 变化，训练 Event Predictor，并用 GES 调节事件密度影响。

这不是人类偏好学习。若后续引入专家 A/B 轨迹偏好，必须单列 `Preference Reward Model` 研究分支，不得混入 T-00～T-05 主线，也不得替代硬约束。

## 5. 不做事项

- 不用预测图覆盖真实 belief。
- 不让 event logits 默认直连 actor。
- 不让世界模型绕过 action mask 或并发安全链路。
- 不宣称可准确预测不可观测的外生随机事件。
- 不在单步模型未校准前开展长时域 imagined planning。
- 不把自动事件监督描述为人类偏好。
- 不在没有测量时宣称降低计算量或延迟。

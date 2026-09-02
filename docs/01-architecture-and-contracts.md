# 架构与数据合同

## 1. 因果转移合同

```python
Transition(
    episode_id,
    scenario_id,
    seed,
    decision_time,
    graph_t,                   # 决策时可见 belief 图
    received_evidence_t,       # decision_time 前已到达证据
    executed_action_t,         # 实际确认执行的候选边或 NOOP
    execution_result_t,
    reward_t,
    cost_vector_t,
    graph_tp1,                 # 下一决策时刻可见 belief 图
    continuation_t,
    auto_event_tp1,            # 只由 graph_t -> graph_tp1 生成
    semantic_label_tp1,        # 可选离线审计/辅助头
    entity_valid_mask,
    feature_valid_mask,
    event_eligible_mask,
    sequence_padding_mask,
    decision_time,             # 当前决策时刻已知；next_decision_time 只作离线目标
    state_version,
    graph_version,
    action_version,
    schema_version,
)
```

训练、验证和测试必须按完整 `episode/scenario/seed` 分组切分。禁止把同一轨迹的相邻 transition 随机拆入不同 split。

## 2. 输入白名单与拒绝项

允许：

- 当时可见的 UAV、Region、Target 节点和关系；
- 决策前已经收到的 evidence/message；
- 实际执行动作、执行结果、当前 `decision_time` 和版本；
- 实体/字段有效性与 padding mask；
- 由训练 split 或物理合同冻结的归一化范围。

拒绝：

- 未到达报文和未来确认结果；
- `graph_tp1`、未来 action mask 或未来动作；
- 动作执行后才能知道的 `next_decision_time - decision_time`；
- 仿真器 truth-only 事件发生时间；
- 最优规划器答案；
- validation/test 的统计量；
- 未确认执行的 policy proposal 冒充 executed action。

## 3. 模态与自动事件

| 模态 | 例子 | 事件目标 |
|---|---|---|
| ordinal | 位置、距离、负载、优先级、confidence、delay | DOWN / SAME / UP |
| nominal | alive、任务类别、assigned UAV、确认状态 | SAME / CHANGED 或类别转移 |
| structural | 节点、关系、候选边、mask support | ADD / REMOVE / REASSIGN / ENABLE / DISABLE |
| evidence | 新消息、重复、冲突、确认、过期 | 独立多标签事件 |

阈值、range、类别组和 eligible mask 只能从物理合同或 train split 冻结，并写入 schema/config 哈希。自动事件生成必须 deterministic；相同输入应产生 byte-identical 结果。

## 4. 世界模型结构

```text
typed graph encoder E_g(G_t)
action encoder E_a(a_t)
evidence encoder E_e(m_t)
               │
               ▼
action-conditioned temporal dynamics
        h_t = f(h_{t-1}, z_{t-1}, E_a, E_e)
        z_t ~ q/p(z_t | h_t, E_g)
               │
               ▼
[next graph/delta, event heads, reward, costs, continuation, uncertainty]
```

建议损失：

```text
L_WM = λ_graph L_graph
     + λ_dyn L_dyn/KL
     + λ_event Σ_m β_m w_GES(m,t) L_event(m,t)
     + λ_reward L_reward
     + λ_cost L_cost
     + λ_cont L_continuation
```

GES 按模态的有效、可产生事件字段计算密度，不对全图使用单个未经审计的比例。先实现可解释的 hard gate，再将 smooth weighting 作为消融。

## 5. 输出与运行状态

```python
WorldModelOutput(
    latent_h,
    latent_z,
    next_graph_or_delta,
    auto_event_logits,
    semantic_event_logits,     # 可选且与自动事件分头
    reward_prediction,
    cost_prediction,
    continuation_probability,
    epistemic_uncertainty,
    aleatoric_uncertainty,
    model_version,
    input_graph_version,
    valid,
)
```

`valid=false`、超时、版本不一致、OOD 风险过高或异常时，GPPO 必须走原始 no-WM 路径。latent 更新必须与 transition 提交保持事务一致，stale 推理不得污染后续 hidden state。

## 6. 接入 GPPO

T-05 主实验只接冻结 latent：

```text
actor candidate = [uav_emb, region_emb, edge_features,
                   global_graph_pool, adapter(h_t, z_t)]

critic = [global_graph_pool, adapter(h_t, z_t)]
```

adapter 应支持 zero context，使关闭世界模型或加载旧 checkpoint 时恢复原 GPPO 行为。`auto_event_logits` 和 `semantic_event_logits` 默认不直接进入 actor；若研究显式事件风险，须建立单独实验组。

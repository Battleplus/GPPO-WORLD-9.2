# M-10 总验收汇报讲稿（约 10 分钟）

**0:00–0:50｜目标与口径。** 本次交付验收的是仿真会议研发目标，不把真实飞行、生产认证或未确认的返航/换电/充电范围偷偷加入门槛。历史 Release 和负结果全部保留。

**0:50–1:40｜基础任务语义。** 任务到达、真实服务、deadline、移动与能耗、损毁、通信、ACK、版本和 lease 已接到统一环境。策略只使用已收到的公开消息；执行拒绝不会被伪装成策略成功。

**1:40–2:30｜安全与因果。** 展示紧急任务、damage、energy insufficient、disconnect/reconnect 路径。普通 telemetry refresh 不构成事件触发；新版本、fencing、mask 和隐藏能量隔离有测试证据。

**2:30–3:20｜PPO 正确性。** R2 修复了非终止 rollout 的 next-state bootstrap、历史边界和非重规划时的 actor 计算/执行语义。记账区分 environment steps、actor decisions、rollout updates、update epochs 和 optimizer updates。

**3:20–4:20｜公平训练。** R3 在同一五类型表示、同一环境分布和同一评估 tape 下比较 MLP-2、Graph-2、Graph-5、History、World，3 seed、8192 环境步、每 seed 128 optimizer updates。World 没有超过 MLP-2/Graph-2；这是有限矩阵的描述性结论，不是普遍无效证明。

**4:20–5:20｜预测质量。** R2 world model 的 context head 确实受监督训练；R3 冻结它并验证融合策略消费。event/done 标签是下一步 simulator consequence，不能直接解释为未来 replan 需求。event BCE 0.258 高于同指标 0.166 baseline，done BCE 0.266 高于 0.221 baseline；Brier 只同 Brier 比较。

**5:20–6:20｜触发成本。** 同一策略和 tape 的周期、规则、model-risk 对照显示：risk 0.1 每步触发，规则节省 actor/world 调用但 return 下降，model-risk 没有节省。故周期决策保留为当前默认，触发结果作为有效负结果。

**6:20–7:10｜候选冻结。** 基础演示使用 MLP-2 Base seed-1101，选择依据是固定矩阵内描述性 return/吞吐；这是工程候选而非无偏最优。Graph-5 World seed-1101 只做融合展示，不默认启用 model-risk。

**7:10–8:00｜复现与归档。** 展示 checkpoint、源码、配置、tape、日志、恢复状态、逐 seed 结果和 SHA-256 索引。最终服务器复现不训练，只复现两个候选的统一轨迹；旧 Release 不覆盖，训练大文件按已有 Release 索引。

**8:00–9:00｜限制。** 没有稳定算法收益证明；服务器缺少旧 pinned GPPO baseline 的 7 项 skip 单列；延迟是指定服务器仿真测量，不代表真实控制周期；真实部署、返航/换电/充电范围和人工评审未完成。

**9:00–10:00｜结论与请求。** 基础功能和新训练/融合交付已完成，当前默认周期决策最可解释。请只确认三个事项：返航/换电/充电是否本次必需、竞赛任务规模与控制周期、实际汇报日期。确认后再决定是否另立新研究任务。


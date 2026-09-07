# M-10-R2 限制与负结果

- R2 只证明修正后的 PPO/触发执行路径在冻结仿真协议中可运行；不证明收益、泛化、生产安全或竞赛实时性。
- 正式 validation-only 阈值为 0.1，导致 triggered risk 门每步成立，2048 步无 continuation 节省；Graph-5 Triggered 与 Graph-5 World 指标相同。该负结果必须保留。
- pilot 在阈值 0.45 下出现 52/100 continuation，但阈值不同且只用于 pilot，不能与正式矩阵混合解释。
- 世界模型 test event/done BCE 均高于简单训练均值 baseline；不能宣称预测质量全面领先。
- 测试集只用于最终评估；OOD 为合成 tape，异常、stale、timeout 回退不扩大为真实系统保障。
- 仅有 3 个训练 seed、2048 环境步；统计结果是描述性汇总，不是稳定显著性结论。
- 归一化能耗、服务、通信和 deadline 不是实机标定；返航、换电、充电仍待确认。
- 真实控制周期和网络条件未知，所有延迟仅适用于本次服务器与仿真条件。
- 服务器缺少 pinned GPPO baseline，7 项 skip 单列，不能冒充覆盖。
- 历史 Shadow 两项 50 ms timeout 未解决；本轮未修改阈值或把它归因于负载。

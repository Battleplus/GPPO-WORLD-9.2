# R-02：开发读出与真实 adapter 开关诊断

日期：2026-09-05。状态：`completed_development_diagnosis_local_only`。

按 [9 月 5 日修订规划](../../docs/10-revised-experiment-plan-20260905.md) 的第一项执行。已完成 12 个冻结模型 × 5 个读出视角，以及 9 个冻结策略 × 12 条开发 tape × adapter 开/关的 216 episodes。没有重新训练世界模型或策略，没有运行 J-01/T-05 Test，没有修改历史门槛。线性读出器在旧 Train 上拟合，旧 Validation 作为已使用的开发数据。

- [固定运行协议](protocol.json)
- [结果与解释](evidence/final-report.md)
- [逐组逐 seed 汇总](evidence/aggregate-results.json)
- [核验记录](evidence/verification.json)
- [原始产物、本机封存归档及 SHA-256](evidence/artifact-locations.json)
- [读出运行清单](evidence/readout-run-manifest.json)
- [adapter 运行来源](evidence/adapter-provenance.json)

程序：[离线读出](../../tools/run_r02_readouts.py)、[adapter 真开关](../../tools/run_r02_adapter_intervention.py)。执行源代码已在本地提交 `41d4fe7` 冻结；结果保存在独立目录，不覆盖旧训练产物。本节点尚未发布 GitHub Release，不能宣称完成远端下载核验。

后续优先级：J-02A 的 pre/commit/next 阶段观测与合法动作事实重放合同。J-02B/J-02C/P-01/T-06 尚未执行；本节点不构成启动策略扩展的效果门槛通过证明。

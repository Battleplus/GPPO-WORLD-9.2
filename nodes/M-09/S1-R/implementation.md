# S1-R 实现说明

修正版工具在 `tools/run_s1_r_acceptance.py`，以原 S1 tape factory 和冻结 checkpoint 为输入。`gppo_world/s1_r_contracts.py` 提供统一 EnergyLedger、生命周期分类、重分配和低置信度确认规则。人工约束探针单独写入服务器报告。

本修正没有改变旧 checkpoint 的输入维度或动作空间；它只修正验收执行器和证据分类。任何未来若改变策略输入或动作空间，需建立新 checkpoint，不可声称旧策略已学会新能力。

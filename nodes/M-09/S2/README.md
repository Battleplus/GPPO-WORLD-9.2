# S2 延迟基准、瓶颈定位与低风险优化

本目录只覆盖 S2，不训练、不进入 S3。正式测量对象是 S1-R2 修正版三类型 GPPO-Adaptive 链路：固定 seed1101、50000 accepted decisions checkpoint、6 类固定场景、每类 10 条 tape。

正式测量协议见 [protocol.md](protocol.md) 和 [protocol.json](protocol.json)，计时边界见 [measurement-boundaries.md](measurement-boundaries.md)。服务器先完成基线，再按冻结协议交错比较最多两项低风险优化。五类型模型、普通 PPO 和“两类型重构”没有同条件可复现实验资产，不作为本阶段性能结论。

正式服务器结果已完成：CPU 与单卡 `cuda:0` 各有 baseline/优化臂 5 遍正式重复、每遍 60 条 tape，另有各 3 次独立冷启动。主要瓶颈是策略前向；唯一采用的优化是 `GraphActorCritic.act` 使用 `torch.inference_mode()`。没有证据支持第二项优化。

没有竞赛控制周期，因此只报告绝对耗时、分位数和配对相对变化，不宣称实时性达标。入口：[comparison.json](comparison.json)、[correctness-report.md](correctness-report.md)、[server-evidence.json](server-evidence.json)、[final-report.md](final-report.md)。

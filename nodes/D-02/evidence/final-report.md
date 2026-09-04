# D-02 开发诊断结果与 D-03 假设判定

日期：2026-09-04。结论：诊断和非干扰 Gate 通过，但不构成世界模型带来策略收益的证明。

## 实际执行

- 代码提交：`70f5763b122de077c79d6304abd4632cccf7139f`，协议在执行前提交到 GitHub；
- WM-GPPO、EA-noGES-GPPO、EAWM-GPPO 三组 × seeds 1101/2202/3303；
- 固定使用 T-05 的 9 个 50k checkpoint 与对应 T-03 世界模型，未训练、未改参数；
- 新开发带：single/sequential/overlap/burst 各 3 条，每带 5 个事件，原 Test 的事件带哈希及初始/事件 seeds 重叠均为 0；
- 108 对 probe-on/probe-off，共 216 episodes，623 条带探针决策；
- 全部配对的非诊断决策字段、奖励、graph version 和最终含 action version 的环境快照完全相同；
- 世界模型对真实环境/belief/mask/version 和动作提交接口写入均为 0，探针不修改非法 logits 或真实 mask；
- 模型文件哈希和策略 state dict 保持不变；
- 独立复核：270 个清单文件、216 条 episode traces、623 条探针记录通过；
- 第一次冻结实验即通过，没有失败尝试或被覆盖运行。

运行环境为 Windows CPU、Python 3.14.4、PyTorch 2.13.0+cpu，与原 Linux CUDA 正式实验不同。这是开发诊断，不是原 GPU 指标的数值或延迟复现；未放宽原 Shadow timeout gate。

## 主要观察

下表汇总三个 seeds。动作分歧是同一 checkpoint 的共同训练 base 分支与加上 adapter 后的首选合法动作之差，**不是与独立 GPPO 模型比较**。

| 组 | 决策数 | 有效 latent 使用 | 首选动作改变 | 使用时合法概率 TV 均值 |
|---|---:|---:|---:|---:|
| WM-GPPO | 209 | 173 | 41 | 0.03120 |
| EA-noGES-GPPO | 208 | 172 | 33 | 0.03019 |
| EAWM-GPPO | 206 | 170 | 17 | 0.02865 |

TV 是合法动作概率分布的总变差距离，范围 0～1。EAWM 在使用 latent 的 170 次决策中有 17 次改变首选动作；其中只有 124 次存在两个以上合法动作，单合法动作时本来就不可能改变选择。

全部 108 次未使用都对应每个 episode 的初始化（`episode_reset`）。本开发样本没有自然触发 OOD/不确定度/timeout/stale 回退，不能据此宣布这些风险不存在；对应原因的记录与不干扰路径已做单元测试，T-04 故障注入证据仍单独适用。

九个 run 的平均 legal actor residual L2 为 0.195～0.294；critic residual 均值为 -3.83～-4.98。后者说明 adapter 对 value 有明显偏移，但 value 的尺度依赖各自共同训练的 base；未对齐真实回报目标前，不能把负偏移称为 critic 失效。

## D-03：哪些假设获得支持

| 假设 | 当前判定 | 依据与边界 |
|---|---|---|
| latent 根本没进入策略/adapter 完全没起作用 | 本开发样本中不支持 | 515 次有效使用；三组都有非零概率变化和动作分歧 |
| 当前开发样本主要被异常回退吞掉 | 本开发样本中不支持 | 108 次回退均为初始化；样本仅 12 条共享 tape，不能泛化到压力场景 |
| 正式奖励统计口径放大了部分表面差距 | 存在口径差异，尚不能归因为模型缺陷 | D-01 已验证事件归因与全部决策 return 不同；本次双口径守恒仍通过，不改旧正式指标 |
| actor/critic 适配器耦合或 latent 表征分布导致收益不稳定 | 尚未确定，保留为后续假设 | actor 确实影响动作，critic 存在偏移；没有随机干预或独立重训对照，不能判因果 |
| GES 本身导致性能下降 | 未证明 | 不能仅凭三个已训练 checkpoint 和 12 条开发 tape 进行归因 |

因此本次不修改 GES、不减弱安全 gate、不把旧 Test 用作调参集，也不直接启动 T-06。下一步先做固定权重的开/关 adapter 验证，再考虑独立的历史对照和训练实验，见 [D-04 协议](../../D-04/README.md)。

## 证据

- [实际摘要](summary.json)
- [逐决策诊断](decision-probes.json)
- [开关配对清单](paired-noninterference.json)
- [开发带 seeds/hash](development-bank.json)
- [代码与环境身份](provenance.json)
- [独立复核](independent-verification.json)
- [失败记录](failed-runs.json)
- [原模型/配置清单](../../T-05/evidence/server-run-manifest.json)
- [完整原始 traces 与审计 Release](https://github.com/Battleplus/GPPO-WORLD-9.2/releases/tag/d02-adapter-diagnostics-v0.1.0)

原模型从 T-05 和 T-03 Release 获取；本次 Release 不重复上传 checkpoint。原始目录 inventory 中的 checkpoint 条目用于核对输入身份，本次诊断归档的实际成员另有独立清单。

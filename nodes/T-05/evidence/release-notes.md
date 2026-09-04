# T-05 frozen-latent GPPO ablation v0.1.0

本 Release 封存 GPPO、WM-GPPO、EA-noGES-GPPO、EAWM-GPPO 四组 × 三 seeds 的正式训练与固定 held-out 评估证据。

- 12/12 个 50,000 accepted-decision run 完成；
- 24 个 25k/50k checkpoints；
- 12/12 个固定 50k checkpoint 评估；
- 每个评估共享同一有序 100-tape Test bank，共 1,200 条 trace；
- belief、action mask、graph/action version 和 Shadow 动作提交写入均为 0；
- 9 个世界模型组的 Shadow 延迟门禁全部通过；
- checkpoint、trace、配置、Test bank 与 Release 资产均有 SHA-256 清单。

结论：接口与安全迁移通过，但四组消融不支持“世界模型稳定提升 GPPO”的普遍性能声明。完整解释见仓库内 `nodes/T-05/evidence/final-report.md`。

本 Release 不包含 T-06 imagined rollout 或人类偏好奖励。

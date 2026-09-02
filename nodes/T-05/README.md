# T-05：冻结 latent 接入 GPPO

**状态：blocked by T-04**

## 目标

通过可选 adapter 将冻结的 `[h_t, z_t]` 接入 GPPO actor/critic；保持候选边、NOOP、真实 action mask、版本校验和执行安全链完全不变。

## 接入原则

- 世界模型参数冻结，先只训练 adapter 与 GPPO；
- adapter 支持 zero context 与配置关闭；
- 旧 GPPO checkpoint 可加载；
- event logits 不进入论文对齐主组 actor；
- invalid/uncertain/stale 时使用原 GPPO 路径；
- 世界模型不写 belief、mask、ACK、lease 或 fencing。

## 最少对照

- GPPO；
- GPPO-History；
- WM-GPPO；
- EA-noGES-GPPO；
- EAWM-GPPO。

所有组使用相同动作空间、mask、奖励、训练预算、seed、事件带和评估脚本。

## Gate

- zero-context/no-WM 与原 GPPO 在冻结容差内等价；
- 旧 checkpoint 兼容；
- 非法动作、stale 漏拦截和并发不变量不退化；
- 性能结论在 held-out 场景和逐 seed 结果中可复现；
- 关闭 WM 能无损回退；
- 每组 checkpoint/config/log/metrics/source commit 可追踪。

## 基础迁移结论

T-00～T-05 和总体验收定义全部通过，即可声明“世界模型基础迁移完成”。不能把计划、单次最佳 seed 或 predicted return 当成完成证据。

## 解锁

通过后才可选解锁 [T-06](../T-06/README.md)。

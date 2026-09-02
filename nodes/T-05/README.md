# T-05：冻结 latent 接入 GPPO

**状态：in_progress（本地接口 Gate 已通过；正式服务器/GPU 消融尚未执行）**

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
- WM-GPPO；
- EA-noGES-GPPO；
- EAWM-GPPO。

`GPPO-History` 是可选解释性对照，不属于当前用户冻结的四组最低验收矩阵。

所有组使用相同动作空间、mask、奖励、训练预算、seed、事件带和评估脚本。

## 已实现接口

- `gppo_world/gppo_adapter.py`：17 动作 residual actor/critic adapter；invalid、zero、stale、disabled 时直接返回原 GPPO 张量；
- `gppo_world/gppo_shadow_env.py`：只在执行层确认后用 `graph_t + executed_action_t + decision-time evidence_t` 更新 latent，供下一次决策使用；
- `gppo_world/gppo_trainer.py`：每条 rollout 保存 immutable latent、graph version 和 action version sidecar，PPO shuffle/update 使用同一份上下文；
- adapter checkpoint 和旧 `random-event-gppo-v1` checkpoint 均有专用恢复路径；恢复时永不恢复跨 episode hidden/context；
- 固定基线的 command-rejection 分支缺少 `env.noop_action`，T-05 只安装 `action_space.n-1` 常量兼容垫片，不改基线提交或运行态 belief/mask/version。

本地 12-transition smoke 使用真实 EAWM Release checkpoint。21 项接口 Gate 全部通过：zero/off 与旧 GPPO bit-exact，12 次 Shadow 有效，23 条 decision-time 已确认 evidence 被读取，真实环境/belief/mask/version 变化和 Shadow action submission 均为 0，stale 与执行拒绝均未进入 Shadow。执行拒绝时，GPPO 仍保存 sampled proposal、原 log-prob、reward 和 next state，把执行层拒绝视为环境动力学结果；世界模型不接收未确认 executed action，下一步 zero-context 回退。详见 [local-interface-validation.json](evidence/local-interface-validation.json)。这不是性能实验，也不能把 T-05 标记为 passed。

## 冻结服务器协议

- 四组 × 3 个 seed（1101/2202/3303）；
- 每 run 50,000 accepted decision steps；25,000/50,000 保存 checkpoint；
- Python 3.10/3.11，CUDA 必须可用；GPPO 在 GPU，T-04 的 CPU immutable Shadow contract 保持不变；
- 同一 train mode cycle、奖励、PPO 超参数、seed namespace 和 100 条 held-out Test tapes；
- 固定 50k checkpoint，不使用 Test 选 checkpoint；
- 输出 commit、环境、GPU、数据/配置/checkpoint SHA-256、history、进度、安全审计和完整 inventory；
- 结果回传 GitHub Release 后才生成四组逐 seed/paired/bootstrap 报告。

冻结配置见 [server-training-config.json](server-training-config.json)，单 run 训练、held-out 评估和聚合入口分别是 `tools/run_t05_server_training.py`、`tools/evaluate_t05_server_checkpoint.py` 和 `tools/aggregate_t05_server_results.py`。
服务器准备、12-run 命令、固定 50k 评估和 Release 回传步骤见 [SERVER_RUNBOOK.md](SERVER_RUNBOOK.md)。

当前机器已只读探测 9 个既有 SSH 配置目标，没有可批量登录且能返回 GPU 信息的主机，因此正式 12 个 run 尚未启动。这个外部算力阻塞不影响本地接口代码，但阻止 T-05 通过。

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

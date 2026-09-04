# T-06：1～3 步 imagined rollout

**状态：planned / optional（T-05 已通过，本节点尚未开始）**

## 目标

在基础迁移完成后，让世界模型仅对 GPPO 提出的合法候选动作做短期潜空间 rollout，研究有限的预测规划/想象训练收益。世界模型仍不拥有环境执行权限。

## 范围

- 先 horizon=1，再 horizon=3；
- horizon=5 只用于误差和漂移审计，不默认用于训练；
- 按 uncertainty/OOD gate 截断；
- 限制 synthetic/real 数据比例；
- 记录每步候选来源、预测价值、不确定度和最终真实结果；
- 保留纯 T-05 EAWM-GPPO 作为即时回退。

## 对照

- EAWM-GPPO（无 imagined rollout）；
- EAWM-Imagine-GPPO horizon 1；
- EAWM-Imagine-GPPO horizon 3；
- uncertainty gate / synthetic ratio 消融。

## Gate

- 1/3/5-step 状态、reward/cost、event 与 calibration 误差透明报告；
- 收益必须出现在真实 held-out 环境；
- 多 seed 改善，不能只挑最佳 seed；
- 非法动作、stale、belief/mask 写入和并发安全不退化；
- 超出不确定度阈值时可靠截断并回退；
- 额外延迟和资源成本在冻结预算内。

## 拒绝条件

若只提高 predicted return、误差随 horizon 失控、或真实安全/任务指标无独立改善，则本节点标记 failed/rejected，产品路径停留在 T-05。

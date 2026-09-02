# T-03：自动事件、Event Head 与 GES

**状态：blocked by T-02**

## 目标

将 EAWM 的事件感知思想迁移到异构图：从相邻可见观测自动生成事件，训练按模态的 Event Predictor，并用 GES 控制高密度边界对训练的影响。

## 实现

- ordinal：DOWN/SAME/UP；
- nominal：SAME/CHANGED 或类别转移；
- structural：node/edge/relation/action-support 变化；
- evidence：new/duplicate/conflict/confirm/expire；
- semantic event head：如需要，只作为独立辅助/审计头；
- hard GES 主实现，smooth GES 作为消融；
- class-balanced CE/focal 仅使用 train split 统计。

## 公平消融

1. `WM`；
2. `WM + Event (no GES)`；
3. `WM + Event + GES`。

模型容量、数据、seed、训练步数和评估脚本保持一致。Event logits 默认不直接进入 GPPO actor。

## Gate

- 自动事件生成 byte-identical；
- 阈值/range/eligible mask 来自物理合同或 train split 并已冻结；
- macro-F1/AUPRC 和稀有事件 recall 超过频率基线；
- GES 密度与权重可审计；
- 基础 next-state/reward/cost 预测不超过冻结的退化上限；
- 负结果和失败 seed 保留。

## 解锁

通过后解锁 [T-04](../T-04/README.md)。

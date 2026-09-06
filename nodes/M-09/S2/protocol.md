# S2 延迟测量协议（冻结版）

## 测量对象

- 冻结 S1-R2 三类型 GPPO-Adaptive checkpoint；保持 4 UAV、4 Region、3 Target、16 条边动作加 NOOP。
- 使用 S1-R2 原六类固定 tape，每类 10 条；同一 tape 的不同重复是重复测量，不增加独立场景数。
- 每个设备分别测 CPU 和单卡 `cuda:0`，不并行使用两张 GPU。
- batch=1、model.eval()、固定随机种子、确定性 argmax；不修改确认、安全、能量、版本或通信语义。
- 正式采用臂走真实源码 `GraphActorCritic.act` 路径：baseline 保持 `no_grad`，优化臂使用 `inference_mode`；direct forward 分段仅作为辅助仪器对照，不替代 source-act 结果。

## 采样

- 每个设备、每个比较臂先 1 遍全 workload 预热，不计入结果。
- 基线和单项优化按重复编号交错执行；每个臂正式 5 遍，每遍 60 条 tape。
- 至少 3 次独立进程冷启动，单列模型加载时间。
- 单次比较臂墙钟上限 60 分钟；超时保存已完成结果并标记 incomplete。

## 时钟与同步

使用 `time.perf_counter_ns()`。CPU 记录完整墙钟时间；GPU 在前向前后调用 `torch.cuda.synchronize()`，因此 GPU 前向包含同步成本，不把异步发射时间冒充完整推理时间。

## 统计

记录每次决策和每条 tape 的原始数据，计算均值、P50、P95、P99、最大值、样本数和超时数，并按场景、tape、重复分层。P99 在样本数不足 100 时标记为不稳定；配对差值以 tape 为组，不把决策样本当独立 tape。

## 采用标准

优化必须在同一 checkpoint、输入和设备上保持 logits、动作、mask、版本、reward、能量、确认、重试和结束分类一致，并在 S1-R2 60 条验收与专项 fixture 通过后才可采用。没有可信改善或行为退化则保留基线。

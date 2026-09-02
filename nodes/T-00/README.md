# T-00：基线与数据合同冻结

**状态：planned**

## 目标

冻结可复现的 GPPO 运行基线、动作合同、Transition schema、字段白名单/denylist、模态注册表和初始性能/安全预算。random legal、greedy 和现有 GPPO 必须走同一 recorder/replay 通路。

## 交付物

- `baseline_manifest.json`：源提交、依赖、硬件、seed、测试命令；
- `schema.json` 与 feature/modality registry；
- 输入白名单、truth-only denylist、版本与时间语义；
- 动作合同：候选边/NOOP、proposal/executed/ACK 的区分；
- 基线 GPPO checkpoint inventory 与可加载性报告；
- 初始延迟、安全和任务指标，用于冻结后续 Gate 数值。

## Gate

- 所有在线输入都能证明在 `decision_time` 可见；
- `executed_action` 不能被 raw proposal 替代；
- future graph/mask、未到达消息、truth-only 字段测试必须拒绝；
- 同一轨迹通过 recorder 重放得到一致样本；
- 原 GPPO forward、保存/加载和最小训练通过。

## 保存点

通过后登记 source commit、schema/config 哈希、基线 checkpoint 哈希、测试日志和固定 tag；这些证据尚未产生，不在本页伪填。

## 解锁

所有 Gate 通过后解锁 [T-01](../T-01/README.md)。

# 根因报告

## 因果时序

旧验收器把 `submit_action` 返回的 `info.new_events` 与动作前的 `decision_time` 比较。环境在 step 内推进时间并在返回时交付新观测，所以这种比较把合法的动作后观测误报为策略泄漏。复核后将评估事件记录与决策上下文分离，并用固定模型配对测试检查完整 graph、logits 和确定性动作：事件到达前两案完全相同，到达后才允许不同；本地结果为通过。

任务说明将原计数称为 30 次（UAV 损毁 10、复合场景 20），但当前仓库保存的旧文字报告写成 20（10+10），旧 JSON 汇总又写成 0，三者版本并不一致，且旧归档没有保留可逐项复算的完整 trace。因此不能把“30”伪装成已由旧归档逐项重算。能被代码和新配对证据确认的真实归因是：这类计数来自动作执行后的合法观测/评估记录与旧决策时刻的错误比较，不是模型在决策前读到了未来事件；修订审计后固定 60 条的 future-input 计数为 0。

## 低置信度

原复合 tape 的弱 Region vacancy 带有 `confidence=0.55`、`severity=0.55`，但随机事件到 TruthEvent 的转换丢弃了 payload，随机事件 detector 又使用硬编码 0.95；同时 Region vacancy 的证据数要求为 1，导致弱信号可被单源确认。修复包括：保留 payload、让 detector 消费 payload confidence、把 observation payload 原样保留，并规定低于 0.95 的 Region vacancy 至少两个独立来源。原 tape 现在显示 0.55 且保持 SUSPECTED；新增两源 fixture 单独显示 CONFIRMED。

## 变更边界

修复在隔离基线分支 `s1-r2-payload-confidence` 提交 `f53efbf95db49ca826b7902b2577217e378d2d96`；冻结基线 `2a9bb9f87b9d543df144f4d108ba970c924151f9` 未被改写。策略 checkpoint 未重新训练、未改变动作空间或输入维度。

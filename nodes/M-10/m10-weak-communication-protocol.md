# M-10 弱通信协议与 tape 冻结

最新冻结参数及具体测试例子见[弱通信场景说明](../../docs/12-weak-communication-scenario-explained-20260910.md)；本文下方历史协议按原日期与run-id解释。

日期：2026-09-07。本文对应弱通信扩训运行 `20260907-weak-comm-v1`，不改写 M-09、M-10、M-10-R、M-10-R2、M-10-R3 或会议总验收历史。

## 对照边界

A 是 Graph-5 Base、每个环境决策周期运行 actor；B 是同一 Graph-5 公开输入/动作/奖励/门禁下消费同一个冻结 world model、每周期决策；C 使用同一 world model 和策略协议，但只在公共语义事件、安全强制、最大等待或模型风险条件下额外重规划。三组不使用 MLP，不改变图类型、任务容量、动作空间、奖励、训练 tape 或评估 tape。C 的 actor 决策次数可以较少，但环境交互预算仍相同。

## 链路与故障定义

遥测、命令、ACK 是三条独立逻辑链路。服务时钟的真实 damage/disconnect/reconnect 在发生时改变执行状态；策略只能在遥测消息实际送达后观察到公开状态变化。命令丢失不会到达 bridge，ACK 丢失不会撤销已经由 `TaskExecution` 接受的唯一命令；控制端不自动重传，后续重新分配仍须通过新的可见版本、mask、ACK、lease 和 fencing 检查。

本轮 composite 仿真参数（时间单位为模拟秒，不是实网测量）固定为：遥测额外延迟 0.5、随机遥测丢包概率 0.15、重排窗口 0.75、遥测 outage `[3,5)` 与 `[10,12)`、命令丢失概率 0.05、ACK 丢失概率 0.10。重复/重排/丢弃决策以 `seed + link + semantic identity` 的 SHA-256 地址化随机流产生，不因某一组命令数量变化而错位。无自动 retransmission，计数明确为 0；物理字节量未建模，审计工具只报告 canonical JSON UTF-8 字节代理，不能解释为真实网络吞吐。

按单因素到复合因素冻结为 `telemetry-delay`、`random-loss`、`burst-loss`、`reorder`、`recovery` 和 `composite` 六级。训练、validation、历史回归 test、最终 test、OOD 分别生成独立 tape ID；历史 test 只作回归，最终 test 不参与预算、模型或阈值选择。原固定 seed-0 regression scenario 继续保留。

## 执行合同

断联在 `ServiceClock` 的事件边界生效并中断该 UAV 上的服务；控制端只有在合法遥测到达后形成新公开快照。任务释放由执行/时钟状态完成，恢复后必须重新满足可见版本、mask、资源状态、租约和 fencing；长期失联自主执行、返航、换电、充电不在本轮动作空间内，也不会通过 NOOP 或续租暗中实现。

非重规划步只续用已 ACK 的 fenced lease，不创建新的分配命令、不重复扣费、不绕过 `TaskExecution`；历史隐藏状态按同一 episode 边界清零。安全条件优先于风险和最大等待，普通遥测刷新不作为事件触发。所有触发原因在更新 `steps_since_replan` 前记录，多个条件同时成立按代码中的固定优先级归因。

## 验收证据

本段保留历史版本口径：本地弱通信定向测试为 6 passed，全套在仓库内受控 basetemp 下为 167 passed；服务器专用目录的直接合同审计为 9/9 passed。加入过期遥测后，最新对应口径为本地 168 passed、服务器直接合同审计 10/10；本轮消息账本修正后的服务器直连新增诊断测试为 2 passed、当前合同直连审计为 11 passed。服务器没有安装 pytest，以上直连数字不冒充服务器 pytest 全套。不同版本数字不可混写。正式训练前已经验证消息延迟可见性、乱序旧消息不覆盖新状态、命令丢失不进入执行、ACK 丢失不造成第二次 accepted execution，以及过期消息不进入策略视图。

当前诊断还为每个遥测 packet 保留稳定 `message_id`，重复投递用 `delivery_ordinal` 表示；完整链路、可行性阶梯和近零完成根因见 `m10-weak-communication-availability-diagnostic.md`。该诊断未新增训练，且弱通信可用性 gate 未通过。

训练和最终评估的详细通信、恢复、执行和端到端时延审计由 `tools/evaluate_m10_weak_comm_details.py` 生成；它只消费已冻结 checkpoint/tape，不训练、不选择模型，所有原始逐 episode 样本保留。

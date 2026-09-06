# S1-R 验收修正与复核

状态：`blocked`

本独立修正版以 S1 固定提交 `0bcbcdb7475cabe9cfc69f6fcd9e51aaa0519cde` 锁定的三类型 GPPO-Adaptive checkpoint 为起点，未修改旧 S1 提交、Release 或原始 60 条结果。修正工具为 [tools/run_s1_r_acceptance.py](../../../tools/run_s1_r_acceptance.py)，契约和回归测试为 [gppo_world/s1_r_contracts.py](../../../gppo_world/s1_r_contracts.py) 与 [tests/test_s1_r_contracts.py](../../../tests/test_s1_r_contracts.py)。

服务器重新执行了原固定六类、每类 10 条、共 60 条 tape；没有训练。完整逐决策轨迹、执行层探针、工具和契约保存在 [m09-s1r-server-artifacts-20260906.tar.gz](m09-s1r-server-artifacts-20260906.tar.gz)，SHA-256 为 `d160fcb03d8e5a54cf0a2e963211e59d529be90482ba665f965e846d3f902f97`，二次下载校验相同。摘要见 [s1r-summary.json](s1r-summary.json)，逐 tape 清单见 [trace-manifest.json](trace-manifest.json)。

## 实际复核结论

- 60/60 episode 正常结束；任务完成按真实环境状态、待处理区域、事件队列和紧急目标状态计算，不能由 `terminated` 替代。60/60 的真实任务状态清空，但不代表六类功能全部通过。
- 正常、紧急、通信中断场景的针对性断言通过。紧急任务记录到达、响应时间、完成状态及 deadline 判定。
- 能量不足场景自主策略发生 10 次能量拒绝；执行层探针另行验证低能量拒绝、stale 拒绝、重复提交不重复扣费。探针不计入自主策略完成率。
- 通信中断 10/10 检测到 stale 拒绝；重试使用新决策和同一执行约束入口，按真正接受的 UAV 扣费。
- 重分配按分配关系的前后变化统计并排除首次分配；复合场景记录 10 次真实变化。
- 复合三因素场景 10 条均保留失败：检测器确认状态不足以证明低置信度行为，且原固定 tape 暴露了发生/可见时间晚于当前决策的事件（未来输入计数 20）。因此 S1-R 为 `blocked`，不能宣称六类验收通过。
- UAV 损毁场景也暴露 10 次未来事件输入计数；该问题已作为真实失败证据保留，不通过改 tape 消除。

下一步仍停留在 S1-R；未进入 S2。返航、换电/充电、五类型图和新训练不属于本修正版。

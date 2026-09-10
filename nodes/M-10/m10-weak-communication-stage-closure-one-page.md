# 弱通信当前结论（一页汇报版）

更新：2026-09-10。完整口径见[当前进度](https://github.com/Battleplus/GPPO-WORLD-9.2/blob/execute-r02-20260905/docs/11-current-project-status-20260910.md)。历史负结果保留。

## 当前状态

Graph-5 GPPO、世界模型输入融合、事件触发及训练/复评流程已运行。世界模型稳定收益尚未建立，完整弱通信可用性未通过，`full_goal_complete=false`。

## 最新正式训练

A/B/C各3个seed，每个变体-seed 12,288环境步、48个rollout、192次optimizer更新。每组评估48个episode、288个任务。

| 变体 | 完成任务 | 完成率 | 每episode平均完成 |
|---|---:|---:|---:|
| A：Graph-5 GPPO | 84/288 | 29.17% | 1.7500个 |
| B：A＋世界模型 | 82/288 | 28.47% | 1.7083个 |
| C：B＋事件触发 | 49/288 | 17.01% | 1.0208个 |

B未建立改善证据；C训练期间actor调用减少约39.3%，但任务效果下降。

## CPU补测与恢复勘误

144/144个episode参考字段匹配。CPU、2线程、无预热、不含落盘；A/B/C完整链路mean为1.8967/2.3177/2.1217 ms。C相对B低8.5%、相对A高11.9%；复评actor调用814/818/504，世界模型调用0/818/826。通信代理量未下降，未达到保持效果并降低成本。

任务中断事件12/12/7，合法获知12/12/7，公开候选7/6/2；接管接受事件3/1/0，对应命令3/2/0；符合定义的替代服务恢复事件均为0。各组144个全部场景事件不能作为中断分母。安全仅记录为本次复评的`no_observed_violation`。

## 历史证据与未完成项

旧压力恢复1/96；selected参考严格恢复26/32；完整池四分类172/26/5/53；187中断、170服务恢复、166按期完成是参考分支事件统计，不是GPPO恢复率。边界扫描29中断、27严格恢复。A-only恢复动作选择路线停止，不否认后续独立授权A/B/C已训练。

原训练raw ledger等历史证据仍缺失；CPU复评不能替代。真实通信、控制周期、部署验证、返航/换电/充电范围及人工汇报活动仍未闭合。

来源：[正式训练](https://github.com/Battleplus/GPPO-WORLD-9.2/releases/tag/m10-authorized-resume-fix-v1-20260908)、[CPU复评及勘误](https://github.com/Battleplus/GPPO-WORLD-9.2/releases/tag/m10-local-cpu-replay-20260910-v1)、[当前PPT](https://github.com/Battleplus/GPPO-WORLD-9.2/blob/execute-r02-20260905/nodes/M-10/slides/m10-current-progress-20260910-v1.pptx)。

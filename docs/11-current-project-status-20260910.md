# GPPO＋世界模型无人机任务分配：当前进度

更新日期：2026-09-10。本页统一当前口径；历史报告按原源码、协议、run-id和统计对象保留。文档更新不代表新增训练或实验通过。

## 当前结论

仿真任务环境、Graph-5 GPPO、世界模型输入融合、事件触发及训练/复评流程已经运行。世界模型的稳定收益尚未建立，完整弱通信可用性仍未通过，`full_goal_complete=false`。

训练完成、冻结模型可复现、效果门槛通过、生产可用是不同结论。原服务器中断前进程和输出状态仍未知。本机CPU复评不能补造原训练raw ledger。

## 已完成

- 任务到达、deadline、移动/等待/服务能耗、损毁和通信中断仿真。
- 遥测延迟、丢包、乱序、断联与恢复；命令、ACK、版本、lease和fencing执行合同。
- 并行lease/continuation修复和triggered continuation的critic输入维度修复。
- Graph-5 A/B/C三组正式训练与冻结checkpoint归档，世界模型实际作为融合输入消费。
- 本机CPU 144/144个episode的正式参考字段逐项匹配，并新增恢复指标勘误。

## 最新正式训练及任务效果

来源：[授权恢复修复归档](https://github.com/Battleplus/GPPO-WORLD-9.2/releases/tag/m10-authorized-resume-fix-v1-20260908)。A为Graph-5 GPPO，B增加世界模型输入，C在B上增加事件触发。三组各3个seed（1101、2203、3307），每个变体-seed 12,288环境步、48个rollout、192次optimizer更新。每组评估48个episode，共288个任务。

| 变体 | 完成任务/总任务 | 完成率 | 每episode平均完成 |
|---|---:|---:|---:|
| A：GPPO | 84/288 | 29.17% | 1.7500个 |
| B：GPPO＋世界模型 | 82/288 | 28.47% | 1.7083个 |
| C：GPPO＋世界模型＋事件触发 | 49/288 | 17.01% | 1.0208个 |

B未建立改善证据。C在正式训练期间actor调用分别为7453、7462、7440，continuation分别为4835、4826、4848；约减少39.3%的actor调用，但任务效果明显下降。validation未找到同时保持效果并节省调用的合格阈值，0.45作为负结果对照保留。以上是训练调用记账，不与下表的复评调用混用。

## 冻结模型CPU补测

来源：[CPU补测及勘误](https://github.com/Battleplus/GPPO-WORLD-9.2/releases/tag/m10-local-cpu-replay-20260910-v1)。CPU、2线程、无预热，完整链路计时不含结果落盘。144/144个episode参考字段匹配，不等于重现了原服务器硬件性能。

| 变体 | mean ms | P95 ms | P99 ms | 时延样本 | actor调用 | 世界模型调用 |
|---|---:|---:|---:|---:|---:|---:|
| A | 1.8967 | 2.3536 | 2.6187 | 814 | 814 | 0 |
| B | 2.3177 | 3.1092 | 4.1232 | 818 | 818 | 818 |
| C | 2.1217 | 2.8180 | 3.2930 | 826 | 504 | 826 |

C相对B均值低约8.5%，相对A高约11.9%；actor调用相对A低约38.1%、相对B低约38.4%。通信compact-JSON字节代理A/B/C为17,660,903/17,781,076/17,855,743，C没有下降。不能宣称保持任务效果并降低整体成本，也不能外推GPU加速、真实流量或竞赛实时性。

## 恢复账本：勘误后的口径

数值依据为该Release中的勘误JSON与verification JSON；勘误Markdown v2仅澄清事件数/命令数写法，不改变数值、模型或原始ledger。

| 指标 | A | B | C |
|---|---:|---:|---:|
| 全部场景事件 | 144 | 144 | 144 |
| 有受影响任务的中断事件 | 12 | 12 | 7 |
| 合法获知事件 | 12 | 12 | 7 |
| 公开候选事件 | 7 | 6 | 2 |
| 合法获知后接管接受事件 | 3 | 1 | 0 |
| 对应接受命令数 | 3 | 2 | 0 |
| 符合定义的替代资源服务恢复事件 | 0 | 0 | 0 |

144不是任务中断分母。接受事件占中断事件的比例分别为3/12、1/12、0/7；命令数量不能作为事件率的分母。上述指标按各自定义报告，不能未经关联复核就当成严格递减漏斗。

恢复为0仅指已有ledger中没有符合定义的替代资源服务恢复，不代表真实网络恢复为0。`no_observed_violation`仅适用于本次复评的已记录检查范围，不替代完整历史安全审计、原训练安全账本或生产保证。

## 历史结果的使用边界

| 历史结果 | 正确范围 |
|---|---|
| 历史压力恢复1/96 | 旧策略、旧压力分布的修正恢复统计 |
| selected 26/32 | 参考执行严格恢复；旧32/32未满足同一严格定义 |
| 完整池172/26/5/53 | 两者成功/参考成功旧策略失败/反向/两者失败的episode四分类 |
| 187中断、170服务恢复、166按期恢复完成 | 参考分支事件统计，不是GPPO恢复率 |
| 边界扫描29中断、27严格恢复 | 34条边界扫描中的事件结果，不是原压力总体 |
| 有界课程B/C未启动 | 只指该A-only课程阶段，不能否认其他已完成A/B/C训练 |

T-05三类型UAV–Region旧动作合同、M-09复现和M-10五类型UAV–Task新环境须分开。M-10的History变体不自动补齐T-05原环境下的GPPO-History公平对照。训练资产存在不等于真实竞赛五类型资产或飞行验证完成。

## 仍未完成

- 世界模型稳定任务收益，事件触发保持效果的综合成本收益，完整弱通信可用性。
- 真实通信、任务规模、控制周期、恢复时限、飞控和部署验证。
- 返航、换电、充电最低验收范围及人工彩排、导师评审和汇报日期。
- 原正式训练raw rollout/event ledger、历史完整通信/时延/逐事件安全记录仍缺失。checkpoint包含optimizer_state_dict及recovery_state，不要求必须另有独立文件才能算保存。
- 原服务器中断前进程与输出状态未知。不要据此认定任务已失败或擅自重复启动。

## 下载与复现入口

- [最新训练及修复](https://github.com/Battleplus/GPPO-WORLD-9.2/releases/tag/m10-authorized-resume-fix-v1-20260908)：归档SHA-256 `65a5cf9e4de40d27fc3b928273924396ae571b5b50f1edeefb203fe5fef2b8c2`。
- [迁移包](https://github.com/Battleplus/GPPO-WORLD-9.2/releases/tag/m10-metrics-replay-migration-v1-20260909)：下载`m10-metrics-replay-migration-v1.zip`，SHA-256 `8eeb90691a3d5c4cfb18fbf08adef58ec06f2bced7398a51405e6d48c316e61d`。
- [CPU补测及勘误](https://github.com/Battleplus/GPPO-WORLD-9.2/releases/tag/m10-local-cpu-replay-20260910-v1)：补测v3 ZIP的SHA-256为`2ca1f6922ed052f8e1c5b97a6f7d7fde4473aa9bf938874d4689cf0f86b2da7f`。原勘误ZIP为`da650ae2b7184c52720d48fbc6209b761c2b402081e72fc9dfbc5e208628a52c`，保留不覆盖。
- [当前6页简报](https://github.com/Battleplus/GPPO-WORLD-9.2/blob/execute-r02-20260905/nodes/M-10/slides/m10-current-progress-20260910-v1.pptx)；[历史PPT与版本说明](https://github.com/Battleplus/GPPO-WORLD-9.2/blob/execute-r02-20260905/nodes/M-10/slides/README.md)。

迁移与CPU补测Release标签指向旧main快照`c9ee0018ce11d315d578c7048db8de0a81242764`。GitHub自动Source code压缩包不包含本轮M-10补测源码；应使用指定迁移资产，核对包内manifest和运行说明。最新报告在GitHub上不代表旧main已合并全部实验代码。

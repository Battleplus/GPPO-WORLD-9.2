# 项目资料索引

更新：2026-09-10。按阅读目的组织入口；历史文件和实验制品保持原位置。

## 先看当前结论

| 阅读目的 | 入口 |
|---|---|
| 理解项目、术语与系统设计 | [项目首页](../README.md) |
| 查看最新结果、限制与未完成项 | [统一进度与结果口径](11-current-project-status-20260910.md) |
| 理解弱通信场景及 A/B/C 比较 | [场景说明](12-weak-communication-scenario-explained-20260910.md) / [冻结参数 JSON](12-weak-communication-frozen-settings-20260910.json) |
| 核对 CPU 时延、恢复分母与安全声明 | [CPU 复评勘误 v2](https://github.com/Battleplus/GPPO-WORLD-9.2/blob/execute-r02-20260905/docs/m10-local-cpu-replay-erratum-20260910-v2.md) |

当前训练与复评完成不代表效果门槛通过：B 未建立改善证据，C 未达到保持任务效果并降低成本的目标，完整弱通信可用性仍未通过。

## 下载模型与复现材料

| 冻结版本 | 用途 |
|---|---|
| [正式训练与修复归档](https://github.com/Battleplus/GPPO-WORLD-9.2/releases/tag/m10-authorized-resume-fix-v1-20260908) | A/B/C checkpoint、训练结果与失败记录 |
| [复评迁移包](https://github.com/Battleplus/GPPO-WORLD-9.2/releases/tag/m10-metrics-replay-migration-v1-20260909) | 配套源码、冻结输入、依赖说明和续跑入口 |
| [CPU 复评及勘误](https://github.com/Battleplus/GPPO-WORLD-9.2/releases/tag/m10-local-cpu-replay-20260910-v1) | 144 episode 复评、原始报告、后续勘误与校验资产 |
| [训练制品索引](https://github.com/Battleplus/GPPO-WORLD-9.2/blob/execute-r02-20260905/nodes/M-10/m10-authorized-resume-fix-v1-artifact-index.md) | 文件与实验版本的对应关系 |

复现使用同一冻结归档的源码、模型和配置，下载后按该版本清单校验 SHA-256。CPU 复评不能补齐原训练缺失的逐事件账本，也不代表原服务器性能。

## 读实现与阶段记录

- [当前 M-10 开发分支](https://github.com/Battleplus/GPPO-WORLD-9.2/tree/execute-r02-20260905)：`gppo_world/` 为实现，`tools/` 为运行工具，`tests/` 为测试。`main` 保留早期源码并提供项目首页；两分支不能当作同一运行版本。
- [M-10 阶段记录](https://github.com/Battleplus/GPPO-WORLD-9.2/blob/execute-r02-20260905/nodes/M-10/README.md)：按时间累积的开发日志；其中“当前”“下一步”按原记录日期理解。
- [M-09 基础交付记录](https://github.com/Battleplus/GPPO-WORLD-9.2/blob/execute-r02-20260905/nodes/M-09/README.md)：早期基线、功能验证与汇报材料。
- [全部历史 Release](https://github.com/Battleplus/GPPO-WORLD-9.2/releases)：历史制品与负结果保留，不能以发布日期替代兼容性检查。

## 早期设计与规划

以下是历史设计背景，不替代上方最新结论或冻结实验参数。

- [范围与边界](00-scope-and-boundaries.md)
- [架构与合同](01-architecture-and-contracts.md)
- [执行规划](02-execution-plan.md)
- [模型与证据政策](03-checkpoint-and-evidence-policy.md)
- [实验与验收设计](04-experiment-and-acceptance.md)
- [2026-09-05 重新分析](09-project-reassessment-20260905.md)
- [2026-09-05 修订实验规划](10-revised-experiment-plan-20260905.md)

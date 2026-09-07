# M-10 最终交付制品索引

本索引只定位制品，不把大文件重复上传。完整 R3 训练归档仍由旧 Release `m10-r3-prediction-trigger-learning-v1-20260907` 提供；本轮独立 Release 只增加最终候选复现、当前源码/材料和索引。

## 代码与材料

- 当前源码：本分支最终 commit；复现入口 `tools/run_m10_final_repro.py`。
- 基础演示：`m10-final-acceptance-demo-basic.md`。
- 融合演示：`m10-final-acceptance-demo-world-fusion.md`。
- 讲稿：`m10-final-acceptance-speaker-notes.md`。
- 总表：`m10-final-acceptance-matrix.md`。
- FAQ：`m10-final-acceptance-qa.md`。
- PPT：`slides/汇报-m10-final-acceptance-v1.pptx`，另有独立 validation receipt。

## R3 既有训练与审计

- R3 Release：[m10-r3-prediction-trigger-learning-v1-20260907](https://github.com/Battleplus/GPPO-WORLD-9.2/releases/tag/m10-r3-prediction-trigger-learning-v1-20260907)，归档 SHA-256 `785f2db6cd5303ae5a9f99e846327b62ebba44081349ef57ca3ae9087a74bfb9`。
- R3 formal matrix：`training-results-r3-summary.json` / server `formal-matrix.json`，SHA-256 `582c19e07992795423059cb7a21ba30cfb4fb1512718886b1265410b93eac0f1`。
- 预测审计：`prediction-audit-r3.json`，历史 test 只作回归；final-test 是选择后冻结的新 tape。
- 触发审计：`trigger-comparison-r3.json`、`server-evidence-r3.json`。
- 世界模型训练事实：`world-model-training-r2.json`；R3 不重新训练。
- R2/R3 训练归档内含逐 seed checkpoint、optimizer/recovery state、配置、seed、tape、日志和评估记录；本轮不重复上传同一大文件。

## 最终复现

服务器新目录和两个运行标识写入最终 status/manifest：`basic-mlp2-seed1101`、`fusion-graph5-world-seed1101`。每个 JSON 内含 checkpoint 路径、完整 tape、逐步轨迹、mask、policy version、ACK/lease、事件、能耗、任务分类、actor/world-model calls；复现明确 `training_performed: false`。下载后对每个文件做 SHA-256，Release 只引用已校验文件。

## 复现原则

使用指定服务器专用环境和当前源码；不停止他人任务、不修改共享环境。所有凭据仅通过已有安全渠道使用，仓库及制品不包含凭据。


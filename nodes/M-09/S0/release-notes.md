# M-09 S0 Release notes

本归档保存 2026-09-05 完成的 S0“版本与术语对齐”。

- 锁定基础演示：三类型 `GPPO-Adaptive`，seed 1101，50,000 accepted decisions，checkpoint SHA-256 `8c11eabbba79c3a0adc1785e84c5b793fecc4d3b9299630a2f18a5d8cfa253b1`。
- 当前 GitHub Release 资产摘要与 13 个既有本地下载文件全部匹配；checkpoint 成功 CPU 加载。没有执行新训练或 S1 轨迹验收。
- 五类型 UAV/Task/Region/Target/Event 版本未找到；Task/Event 在现有实现中不是图节点。
- 能量、返航/换电、通用紧急任务和完整三因素复合注入仍为缺失项。
- 服务器只读 SSH 连接超时，当前 GPU/进程/磁盘/软件状态未知。
- S0 状态为 passed；S1 可基于三类型冻结基线启动实现，但尚不具备通过条件。

归档不会覆盖 `m09-delivery-plan-v1-20260905` 或任何旧 T/J/D Release。

# M-09 / S0：版本与术语对齐核查

核查日期：2026-09-05。结论：**S0 通过，基础演示锁定为三节点类型的 `GPPO-Adaptive`，不声称存在会议所述五类型实现。** S1 可以从该冻结基线开始做功能实现与验收；当前版本不能直接通过 S1，因为能量、返航/换电、通用紧急任务和完整三因素注入仍缺失。

## 基础演示锁定

| 项目 | 冻结值 | 证据性质 |
|---|---|---|
| 原始基线 | `Battleplus/GPPO-8.29@2a9bb9f87b9d543df144f4d108ba970c924151f9` | GitHub 当前 main 与本地只读 checkout 一致 |
| 世界模型仓库运行代码 | `69e3be5931deea7371df77d75fb14f2f5bdeab72` | T-05 正式运行清单中的 `target_commit` |
| 基础策略 | `GPPO-Adaptive`, seed 1101, 50,000 accepted decisions | T-05 已有结果；S0 当前复核 SHA-256 并成功 CPU 加载 |
| checkpoint | `gppo_seed1101_step50000.pt` | SHA-256 `8c11eabb...fa253b1` |
| 动作空间 | 16 条 UAV–Region 候选边 + 1 个 NOOP | 源码 `graph.py`、`environment.py` |
| 图类型/实体数 | UAV/Region/Target 三类；固定 4/4/3 个实体 | 源码 `graph.py`、`registry.py` |

选择纯 GPPO 50k 模型，是因为它已有固定配置、三 seed 正式训练、100-tape held-out 评估和 Release 哈希证据，并且不依赖世界模型 checkpoint。T-05 证明了世界模型接入和回退，但没有证明稳定策略增益，因此世界模型组不作为本阶段基础演示默认模型。完整命令见 [demo-runbook.md](demo-runbook.md)，资产来源见 [version-inventory.json](version-inventory.json)。

## 实际核查结论

- **当前实测：**执行分支在规划提交 `ea6cc588...80d5d` 上起步且工作树此前干净；GitHub API 显示远端 main 为 `c9ee0018...2764`，执行分支为规划提交。规划 Release 标签也精确指向该提交。
- **当前实测：**13 个本地已有 T-05 Release 下载资产全部与 GitHub 当前摘要一致；选定 checkpoint 从归档中提取后 SHA-256 匹配，并以 CPU 成功构造 `GraphActorCritic`，参数量 203,395。此检查不是运行轨迹或性能验收。
- **源码事实：**仓库及原始基线的图构建器、特征注册表和模型更新层只声明 `uav`、`region`、`target`。在现有分支、全部本地/远端分支名和提交信息中未找到 Task/Event 作为节点类型的五类型版本。
- **源码事实：**Task 是 UAV 上的 `SEARCH/TRACK/IDLE` 状态；Event 是带发生/可见时间的事件记录与世界模型监督标签，二者都不是策略图节点。详细语义见 [task-and-event-definitions.md](task-and-event-definitions.md)。
- **已有结果：**T-05 四组平均推理延迟约 3.75–4.22 ms，仅可用于同一 T-05 协议内部描述。没有找到普通 MLP PPO 与会议五类型 GPO 在同硬件、同模型输入、同计时边界下的原始“慢 3～4 倍”测量，因此该说法仍是未验证会议观察。
- **当前实测（2026-09-06）：**VPN 恢复后已成功登录 `user1@172.17.27.173`。两张 RTX 2080 Ti 均为 0% 计算占用、无 compute process，显存占用 6/20 MiB；磁盘可用 293 GiB。`dporl` 为 Python 3.9.20、torch 2.2.2、CUDA 12.1，可见两张 GPU。该空闲状态仅代表检查时刻，不构成资源预留。完整结果见 [server-preflight.json](server-preflight.json) 和 [原始摘要](server-preflight-20260906.txt)。
- **当前实测（备选资源）：**`daji@172.17.27.172` 与 `xiaoji@172.17.27.172` 实际是同一台 8×RTX 4090 主机。GPU 6 连续三次检查均无进程；GPU 4 曾短暂出现 Python 显存占用，因此不是稳定空闲。两账号目录均未找到 GPPO 训练入口或冻结配置，S0 未上传文件或启动训练。详见 [备选服务器预检](server-preflight-alternates-20260906.json)。

## GitHub / 分支 / Release 关系

执行分支包含 GitHub main 当前提交，比较结果为 main 独有 0、执行分支独有 14；没有合并或改写 main。规划 Release `m09-delivery-plan-v1-20260905` 指向规划提交，旧 T-01～T-05、J-01、J-02B、D-02 Releases 均保持独立。本 S0 另建独立 Release，不覆盖旧 tag 或旧测试资产。GitHub API 原始快照保存在 [github-branches.json](github-branches.json) 和 [github-releases.json](github-releases.json)。

## S0 决定与下一步边界

1. S1 使用已锁定三类型 GPPO checkpoint 做基础闭环；任何新增的 Task/Event 节点版本须作为新实现和新模型处理，不能冒充会议既有版本。
2. S1 必须先补齐或明确降级通用紧急任务、能量不足，以及返航/换电行为；完成后才运行规划中的 60 条验收。
3. 通信异常和低置信度已有底层检测/确认机制，但缺少冻结的复合测试控制入口和 S1 轨迹证据，状态仍为待实现/待验收。
4. 服务器当前存在可用 GPU 容量，但按 S0 范围只完成只读预检。正式运行前仍需把冻结源码、配置、数据与输出目录隔离部署，并再次确认 GPU 空闲。本阶段未训练、未执行 S1 60 条验收、未启动 JEPA、未联系群聊。

缺口、影响和处理决定见 [gaps.md](gaps.md)。

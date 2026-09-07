# M-10：完成会议研发目标

建立日期：2026-09-06（北京时间）。中旬汇报日期尚未确认。本节点延续会议研发目标，M-09是基础交付而非研究终点。必须完成新任务语义下策略训练、世界模型配套融合训练及公平比较，不能用历史复现替代。

## 当前核查

### M-10-R2（2026-09-07）

R2 修正并验收了 PPO 非终止 bootstrap、历史状态边界、非重规划 continuation、事件触发语义和 optimizer 记账。新增测试 9 passed；本地全套 160 passed；服务器 153 passed、7 skipped（服务器缺少 pinned GPPO baseline）。服务器 pilot `20260907-r2-correctness-v1/pilot-v3` 证明 triggered 路径有 109 次 actor 决策和 19 次 continuation；同预算正式矩阵 `formal-v1` 为 6 变体×3 seed×2048 steps，每 seed 32 次实际 optimizer steps。

正式 validation-only 触发阈值为 0.1，导致风险门每步成立，triggered 正式测试 continuation 为 0，且与 Graph-5 World 结果相同；这是保留的负结果，不是触发优化收益。世界模型 test 的 event/done BCE 也未优于简单均值基线。详细记录见 `m10-r2-report.md`、`m10-r2-limitations.md`、`training-results-r2-summary.json` 和独立制品 manifest。旧 M-09、M-10、M-10-R Release、训练和失败记录不改写。

本轮实际执行分支为 `execute-r02-20260905`；M-10 本地实现已提交，服务器源码归档 SHA-256 为 `77321bb99bc400f238b7ad505c603f87267f9632ea810a319eee684eaa828ba6`。M-09 S5 冻结 `7a7ab55149cb7da56ee9447799279597ec293477` 与历史归档保持不变；本节点只记录 M-10 新环境、训练和证据。

已完成指定服务器上的 pilot、正式矩阵、世界模型/融合策略和触发敏感性补充；GitHub 独立 Release 在 R5 收尾后记录。训练结果不替代待确认的返航/换电/充电范围、真实五类型资产或真实飞行验收。

基线graph.py明确：旧普通PPO是165维向量和四维MultiDiscrete动作，GPPO是UAV/Region/Target图和UAV–Region边动作。不能用两套原始接口直接宣称同任务公平比较。新普通PPO参照应采用同一新环境与同一离散候选动作，仅改变编码结构。

基线environment.py使用pending_regions、事件队列和区域恢复终止逻辑；graph.py仅pending且capable的边可选。未在这些文件找到energy或deadline实现。因此任务到达、服务进度、截止时间与能量不能只增加几个标签就宣称实现。

## 阶段

| 阶段 | 内容 | 当前状态 / 退出证据 |
|---|---|---|
| R0 | 任务语义和对照合同 | passed；固定公开规模、能量/信息合同及源码来源 |
| R1 | 新任务环境与两/五类型等信息视图 | passed；完整环境因果验收 7/7 |
| R2 | 同环境MLP-PPO、图PPO、图PPO-History训练 | passed；服务器 pilot 与正式三 seed 矩阵 |
| R3 | 监督世界模型与配套融合策略训练 | passed；episode-disjoint 数据划分与实际 context 消费 |
| R4 | 表示、历史、世界模型与触发机制消融 | passed；5 变体、阈值 0.5 负结果和 0.2 敏感性补充 |
| R5 | 下载、归档与更新汇报 | passed；Release 已发布并完成三项资产 CDN 回读校验，不覆盖M-09 |

## R0候选合同（尚未批准为竞赛事实）

Task是有到达时间、优先级、截止时间、所需服务量与状态的工作项；Region是空间位置；Target是目标实体；Event是已到达证据记录。任务分配不等于完成，必须累积合法服务进度，损毁/断联对任务连续性的影响明确建模。

建议先采用归一化仿真能量：移动、服务、等待分别扣费；能量耗尽取消相应执行能力。数值和时间单位在R1实现前冻结，不冒充实测飞行动力学。是否包含返航、换电和充电需用户明确，它们不能通过NOOP伪装。

策略输入只读取已收到遥测和已确认事件，分别保存值、年龄和有效性。真值只供仿真与执行安全，迟到遥测不能直接更新历史输入。合法mask若由隐藏能量计算会泄漏信息，必须区分基于可见状态的提议mask和真实执行层拒绝。

两类型视图将Region/Target/已见Event信息以有明确身份的Task属性/关系表示；五类型视图显式展开。两者必须具有相同声明的可见信息。不能删除信息却把效果归因于类型数量。两类型映射若无法等信息，应单列有损消融。

动作接口候选：UAV–Task分配+NOOP，任务数量有上限和padding mask；新接口与旧17动作checkpoint不兼容，应从头训练。返航/换电若纳入，需显式新增语义和统一对照动作，不在已有模型上强行加载。

事件触发先保持共同的执行安全触发规则；世界模型提供任务后果预测作为策略输入。若要研究模型驱动重规划，另设单因素触发消融：对照同样拥有合法观测、周期和安全强制触发，报告误触发/漏触发、恢复时延与计算成本。仅context消费不能叫触发优化。

## 预算原则

先进行单组服务器计时与训练正确性pilot，记录真实交互和optimizer更新；据此冻结每组相同训练预算、终点、seed及墙钟。不得沿用不匹配旧Test。世界模型数据采集和预训练成本单列。核心模型对照与类型/触发消融分步执行，不直接展开全部因素的笛卡尔积。

所有正式训练在指定服务器；不修改共享环境。每阶段先下载校验，再GitHub存档。当前没有启动新训练。

## 已实现的独立合同组件

`gppo_world/task_lifecycle.py`实现任务到达、分配、累计服务、中断后保留进度及重新分配、截止失效。服务恰在截止时完成算成功；仿真环境必须在损毁/通信/能量变化点拆分服务区间并证明区间可执行。该组件不读策略输入，不代表已经实现完整观测隔离、运动学或能源约束。

`python -m pytest tests/test_task_lifecycle.py -q`：10 passed。覆盖分配不等于完成、失败后换机续作、截止截断、截止边界、到达前拒绝、区间重叠和非法速率。当前尚未接入训练环境。返航/换电/充电范围已向用户发出问题，待答复；继续开展不依赖其动作设计的合同实现。

`telemetry.py`仅存放已到达测量，区分known/valid/age，处理乱序与冲突消息；完整环境仍需确保策略不能访问调度器或真值。

`service_clock.py`按任务到达、完成、deadline、服务能量耗尽及外部事件切分区间，损毁立即中断，断联是否中断由显式参数决定。连接恢复不自动恢复已中断分配。边界约定为先结算截至事件时刻的服务，再应用事件，因此恰在deadline/损毁时刻完成有效。它只计算到位后的服务能耗，不包含移动、等待、返航、充电；资源判断属于执行层真值，不可直接当策略mask。

组件联合验证：`python -m pytest tests/test_service_clock.py tests/test_telemetry.py tests/test_task_lifecycle.py -q`，21 passed。尚未证明原版本ACK/lease/fencing与新组件集成，不得直接以当前ServiceClock替换完整训练环境。

## 后续增量：移动与等待能耗

ServiceClock现已支持二维直线移动、速度、移动功率、等待功率和任务位置。分配后先移动，到达后才累计服务；外部故障、deadline、到达、完成、能量耗尽均切分执行区间。未分配且仍存活的资源消耗等待能量，断联取消执行时也适用；损毁资源停止扣费。任务完成后转为等待。时间、距离和能量为归一化仿真单位，未声称实机物理精度。默认共址/零等待功率仅为旧组件测试兼容值，正式训练必须显式冻结参数。

新增7项运动学测试，覆盖移动/服务/等待分段扣费、途中耗尽、损毁、断联、到达前deadline、等待耗尽及时间切分一致性。本地全套126 passed；服务器独立目录28项组件测试通过（0.05秒）。专用测试环境为 `/home/user1/m10-test-venv`，未修改原s1隔离环境；依赖与日志在 `server-motion-check`。源tar本地SHA为 `1cb1689b95ce4f1c56ba67a181dc119aa8de028a98a58bddb54b2f4638c59dfa`，服务器SHA见下载日志。

本增量仍不包含完整策略观测、动作mask、版本/ACK/lease集成或返航/充电。R0尚未结束、正式训练尚未启动；组件测试通过不能当作完整环境验收。

## 后续增量：任务级执行桥接

`task_execution.py`将任务时钟接入命令/ACK/租约：提议不立即分配；ACK必须匹配命令、UAV、token且未到期；ACK接受前重新检查版本和真实资源条件。重复ID不覆盖旧命令，旧token不能夺回新持有者的任务。服务按租约到期点截断，显式续租要求有效身份及资源，故障/任务结束释放执行租约。接受命令本身不扣一次性虚构能量，能量由真实移动/服务/等待结算。

这是参照旧`event_runtime/concurrency.py`的安全语义实现的任务级适配，不是直接调用旧Region接口。新租约属于Task，同Region内不同任务能否同时执行仍由完整环境资源合同决定。新边界采用ACK/租约到期时刻即失效；先结算截至该时刻的物理服务，再中断，与旧`now > expires_at`需在迁移协议明确区分。确认链尚未接入。环境必须经TaskExecution推进时间和处理传输ACK，不能让策略直接调用ACK、修改clock或访问执行诊断。

本地新增6项测试通过，覆盖ACK身份、重复提交、stale后能量重验、ACK到期、竞争持有者、租约中途失效、续租和断联。完整环境因果/确认/动作mask验收仍未完成；本增量尚未在服务器运行，不代表训练启动。

## 后续增量：可见输入与执行连接

`task_policy_view.py`只接收白名单遥测，不接收仿真对象或未来事件列表。固定公开舰队与任务容量，任务槽按消息实际送达顺序分配，未送达槽固定为零且不可选。每个量保存value/known/valid/age；过期输入保留历史值但禁止提议。候选动作始终是固定UAV×Task槽加NOOP，不根据隐藏未来任务数量改变。版本随实际收到的新信息及决策时间变化，重复消息不会产生新版本。该输入模式尚未包含完整五类型、确认链及训练归一化，不可宣称最终信息合同已冻结。

`task_decision_bridge.py`将已发出的快照与当前合法可见快照比对，只有未过期且mask允许的提议才送入TaskExecution；NOOP与padding不创建分配。桥接返回值属于执行传输诊断，完整模拟器必须按收到反馈时刻将允许信息回送策略，不能即时传递隐藏真值。ACK前还需由完整消息调度器同步最新可见版本；组件不会自行调度传输。

新增10项测试覆盖未到达任务不影响槽/版本/mask、白名单、过期遥测、重复消息、反馈送达后才改变mask、固定动作映射、隐藏能量配对、stale快照、提议至物理完成和NOOP。配对测试证明组件层的特征与mask等价，尚未包含真实策略logits或全环境历史；不得扩大为完整零泄漏证明。

本轮全套结果：140 passed、2 failed（26.78秒），失败为旧Shadow测试 `test_shadow_valid_inference_is_read_only` 与 `test_failed_step_forces_history_reset_on_recovery`，均返回timeout。独立重跑Shadow：4 passed、2 failed（53.04秒），相同两项失败。fixture阈值为50ms，未修改阈值；目前没有证据确定超时根因，不能直接归因于机器负载，也不能声称全套通过。独立重跑的外层PowerShell命令末尾包含文件读取，因此外层退出码0不代表pytest通过，以上以pytest摘要为准。后续需在受控环境复核这些现有时延测试。

## 2026-09-07 实际 M-10 环境与训练结果

本轮新增 `gppo_world/m10_environment.py`，把任务到达、服务进度、移动/等待/服务能耗、deadline、损毁、通信中断、收到的遥测、固定容量 mask、版本化提议、任务级 ACK 和独占租约接入同一仿真时钟。默认协议固定 4 UAV、6 个任务槽、18 个归一化时间单位、25 个动作（24 个 UAV×Task 分配加 NOOP）；返航、换电和充电仍保留为待确认范围，没有静默排除。

服务器实际运行：Python 3.10.12、Torch 2.2.2+cu121、2×RTX 2080 Ti。正式矩阵为 5 个变体、3 seeds（1101/2203/3307）、每 seed 1024 steps；世界模型使用 1059 条 transition，按 episode-disjoint 划分 train 732、validation 165、test 162，test 未用于训练或选择。

| 变体 | 完成数均值 | 过期数均值 | return 均值 | 触发次数/episode |
|---|---:|---:|---:|---:|
| MLP-PPO two-type | 4.00 | 2.00 | 31.071 | 0 |
| Graph-PPO two-type | 4.33 | 1.67 | 35.639 | 0 |
| Graph-PPO-History five-type | 4.33 | 1.67 | 35.685 | 0 |
| Graph-PPO + world context | 4.00 | 2.00 | 31.000 | 11–15 |
| Graph-PPO + event trigger | 4.00 | 2.00 | 30.956 | 5 |

这些是本协议、预算和三 seeds 下的受限结果，95% seed CI、逐 seed 记录和全部 checkpoint 见 `training-results.json`。没有稳定世界模型收益结论。阈值 0.5 的零触发结果作为负结果保存在 Release 归档的 v1 输出中；阈值 0.2 的补充矩阵仅作为触发敏感性结果，不改写 v1。

新增全环境因果验收 7/7；服务器全套回归 139 passed、7 skipped，跳过项均因旧 GPPO baseline 未安装。此前两个 Shadow timeout 在服务器受控环境重跑均 passed（0.85s），原 50ms fixture 门槛没有修改。

训练归档在 [GitHub M-10 Release](https://github.com/Battleplus/GPPO-WORLD-9.2/releases/tag/m10-meeting-research-v1-20260907) 单独发布，仓库只保留协议、结果、证据和清单。完整复现命令见 `nodes/M-10/reproduction-runbook.md`；汇报稿见 `nodes/M-10/slides/汇报-m10-final.pptx` 与同名 PDF。

## 2026-09-07 M-10-R：训练有效性与公平性修正

M-10-R 不改写上述历史结论或旧 Release。针对历史审查发现的 seed 场景不变、缺少 Graph-5 Base、五类型占位 token、世界模型 test_rows 冒充测试评估、context head 未入损失、以及 context gating 触发次数误称重规划等问题，已完成代码修正和新的服务器闭环。详细缺陷分类、结果、限制和待确认事项见 `m10-r-report.md` 与 `m10-r-limitations.md`。

正式服务器运行标识为 `20260907-r-corrected-matrix-v2`：6 变体（MLP-2 Base、Graph-2 Base、Graph-5 Base、Graph-5 History、Graph-5 World、Graph-5 Triggered-Replan）× 3 seed × 2048 steps；每组实际 8 次 PPO optimizer update，18 个 checkpoint。train/validation/test/OOD tape 分别冻结为 64/16/16/16 episodes；验证集选择阈值 0.2，测试集未用于校准或选择。Graph-5 World 与 Triggered-Replan 本轮均值 return 为 30.981，触发组 217 次评估触发全为 `public_event`，不作稳定收益或生产重规划结论。

本地受控全套测试 151 passed，Shadow 定向复核 6 passed；服务器回归 144 passed、7 skipped（既有 pinned GPPO baseline 未提供），新的全环境因果验收 10/10。完整决策链 100 samples 延迟为 CPU 2.872/3.081/3.091 ms（mean/P95/P99），CUDA 3.565/3.786/3.803 ms；测量只代表指定服务器归一化仿真，未知真实控制周期，不宣称竞赛实时达标。

M-10-R 训练归档已下载并双端 SHA-256 校验：`m10-r-training-artifacts-20260907.tar.gz` 为 `bd5d01b52c09b793eb352854822f16e5690748292205ebb501d394afbb91eb4b`。归档同时保留先前失败矩阵目录和修复后的成功矩阵，源码、tape、checkpoint、optimizer/recovery state、日志、逐 seed 结果和服务器测试齐全。M-10-R 独立 GitHub Release 已发布：[m10-r-training-validity-fairness-v1-20260907](https://github.com/Battleplus/GPPO-WORLD-9.2/releases/tag/m10-r-training-validity-fairness-v1-20260907)，三项资产已通过 GitHub API digest 与独立下载复核；不修改 `m10-meeting-research-v1-20260907`、main 或 force push。

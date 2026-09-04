# T-05 正式服务器 Campaign 实时接力存档

> 快照时间：2026-09-03 19:38:31 +08:00。本文记录的是正在运行的正式 campaign，不是最终实验结论。机器可读快照见 [`server-campaign-live-snapshot.json`](../nodes/T-05/evidence/server-campaign-live-snapshot.json)。

## 1. 当前结论

正式 T-05 campaign 已经部署并启动。首批两个 GPPO 对照 run 已完成；两张 RTX 2080 Ti 正在并行运行下一批任务，后台双 GPU worker 已接管剩余训练、固定 50k 评估和最终聚合。

- 正式训练完成：`2/12`；
- 正式训练运行中：`2/12`；
- 固定 held-out 评估完成：`0/12`；
- 聚合：`pending`；
- T-05 状态仍为 `in_progress`，不得提前标记为 `passed`。

快照时的两个运行中任务：

| GPU | Group | Seed | PID/PGID | Accepted decisions | 速度 |
|---|---|---:|---:|---:|---:|
| 0 | GPPO | 3303 | 801696 | 2,048 / 50,000 | 20.94 steps/s |
| 1 | WM-GPPO | 1101 | 801963 | 1,024 / 50,000 | 18.92 steps/s |

两张卡在快照时分别使用约 240 MiB 和 255 MiB 显存，GPU 利用率约 23% 和 24%。GPPO seed 1101（正式目录为 `seed1101-attempt-2`）和 seed 2202 已由 worker 验证完成 50,000 decisions。不要只凭早期 GPPO 对照组的显存/速度推断三个世界模型组的最终资源需求。

## 2. 服务器与 Campaign 身份

训练服务器：

```text
host: 172.17.27.173
hostname: ru-server-MS-1
linux user: user1
GPU: 2 x NVIDIA GeForce RTX 2080 Ti, 11264 MiB each
campaign root: /home/user1/gppo-t05-campaigns/gppo-t05-20260903-135255-hanzhangyang-cdcb23
```

接手者应向用户安全索取服务器凭据；不得把密码、Token、私钥或 API Key 写入仓库、日志或登记文件。

正式冻结身份已经因 Linux CRLF/LF 可移植性缺陷做过统一最小修复。所有正式 run 和 evaluation 必须统一使用以下身份：

```text
target branch: t05-server-linux-fix
target commit: 69e3be5931deea7371df77d75fb14f2f5bdeab72
baseline commit: 2a9bb9f87b9d543df144f4d108ba970c924151f9
server config SHA-256: 973dc586fb0bac268ab753c180b8a19cfe0e01430b3bd9251c91118af4871225
T-03 checkpoint release: t03-eawm-v0.1.0
Test manifest SHA-256: f295bc42ba932ed192162f231670de3865dedae7f2d737331576b90f2cf88bf5
```

服务器执行 checkout：

```text
/home/user1/gppo-t05-campaigns/gppo-t05-20260903-135255-hanzhangyang-cdcb23/run-target-69e3be5
```

精确修复 commit 已发布到 [`t05-server-linux-fix`](https://github.com/Battleplus/GPPO-WORLD-9.2/tree/t05-server-linux-fix)。原目标 `a4432a9` 和中间修复 `21c181e` 都没有产生正式 accepted decision；不得把不同 commit 的 run 混入同一 campaign。

## 3. 已通过的 Gate

- Python 3.10.12；
- PyTorch 2.7.1+cu118；
- CUDA available，RTX 2080 Ti 正常识别；
- 9 个世界模型 checkpoint 文件名与 SHA-256 全部匹配；
- 修复 checkout 上 45/45 tests 通过；
- 21 个 T-05 本地接口/安全 Gate 全部通过；
- legacy/disabled GPPO 回退 bit-exact；
- 世界模型冻结；
- environment、belief、action mask、graph/action version、Shadow action submission 写入均为 0；
- 目标和基线工作树均 clean；
- 唯一正式 100-tape Test bank 的原始文件 SHA 和 canonical tape SHA 全部验证通过；五个 Test 集合各 20 条。

正式 Test bank 复用基线提交中已经完成并带不可变 lock 的银行：

```text
$CAMPAIGN_ROOT/frozen-bank/tapes/preliminary_test_protocol/manifest.json
```

不要重新生成 Test bank，也不要使用 Test 结果选择 checkpoint。12 次评估只能使用各 run 固定的 step=50,000 checkpoint。

## 4. 登记约束

真实姓名与 ID：

```text
real_name: hanzhangyang
name_id: hanzhangyang
campaign_id: gppo-t05-20260903-135255-hanzhangyang-cdcb23
```

中央登记位于另一台服务器：

```text
registry host: 172.17.27.172
registry: /media/abc_disk/admin123/lbh/dengji.txt
lock: /media/abc_disk/admin123/lbh/dengji.txt.lock
```

24 个 job（12 train + 12 eval）已经以 `REGISTERED` 只追加登记并逐条复读验证；当前两个正式训练进程还追加了 `RUNNING`。以后仍必须使用 `flock` 只追加 JSON Lines，禁止覆盖、删除或修改历史记录。不得写入任何凭据。

训练服务器没有挂载中央登记路径。后台 worker 把启动、完成和失败事件写入本地 ledger；接手者应把新增事件核验后补充追加到中央登记文件：

```text
$CAMPAIGN_ROOT/orchestration/gpu0-events.jsonl
$CAMPAIGN_ROOT/orchestration/gpu1-events.jsonl
```

## 5. 自动执行器

两条 worker 已经运行，不要重复启动：

| GPU | Worker PID | 当前接管 PID | 状态文件 |
|---|---:|---:|---|
| 0 | 795129 | 801696 | `orchestration/gpu0-state.json` |
| 1 | 795130 | 801963 | `orchestration/gpu1-state.json` |

worker 脚本：

```text
$CAMPAIGN_ROOT/orchestration/gpu_worker.py
SHA-256: 6cb5f595bdbca9320fbdf83087ff7b49c1eb30661fa9690dc5ace97ca08f0e05
```

它们会执行：

1. 接管并等待当前 GPPO seed 1101/2202 完成；
2. 在两张 GPU 上分摊剩余 10 个正式训练；
3. 每次启动前重验 target/baseline/config/Test manifest 身份和 clean 状态；
4. 若发现该 GPU 上存在其他 compute process，则等待，不杀进程、不抢占；
5. 每个成功 run 强制验证 50,000 decisions、25k/50k checkpoints、done progress、完整 inventory 和安全零写入；
6. 对各自 6 个 run 执行固定 50k checkpoint 的 100-tape 评估；
7. 强制检查每次 evaluation 的 100 traces 和安全零写入；
8. GPU0 worker 等待 GPU1 完成，然后运行 12 份结果聚合；
9. 任一失败立即停止对应队列，写 `FAILED` 状态并保留原目录和日志。

读取状态：

```bash
CAMPAIGN_ROOT=/home/user1/gppo-t05-campaigns/gppo-t05-20260903-135255-hanzhangyang-cdcb23
cat "$CAMPAIGN_ROOT/orchestration/gpu0-state.json"
cat "$CAMPAIGN_ROOT/orchestration/gpu1-state.json"
tail -n 20 "$CAMPAIGN_ROOT/orchestration/gpu0-events.jsonl"
tail -n 20 "$CAMPAIGN_ROOT/orchestration/gpu1-events.jsonl"
nvidia-smi
```

不要只看终端有无输出；训练进度以每个 run 的 `progress/live_progress.json` 为准。

## 6. 已保留的失败与修复

第一次启动 GPPO seed 1101 时，runner 在训练循环前因 T-04 calibration SHA 的 CRLF/LF 差异拒绝执行：

```text
failed run directory: $CAMPAIGN_ROOT/runs/GPPO/seed1101
launcher log: $CAMPAIGN_ROOT/launcher-logs/train-gppo-s1101.log
error: Shadow calibration SHA-256 mismatch
accepted decisions: 0
RUNNING registry event: none
```

该失败目录和日志必须保留。正式重试使用 `seed1101-attempt-2`。修复 commit `69e3be5` 同时把基线 protocol、seed manifest 和 T-04 calibration 的冻结 SHA 改为 clean Linux checkout 的 LF 字节哈希，并增加回归测试。

另一个已披露问题：基线的 `python -m ppo_allocation.random_event.experiment protocol-bank` 不会调用 `main()`；官方 wrapper 随后又会正确执行 Phase J 的“先 freeze、后 Test”保护。此次 campaign 没有绕过该 Gate，而是复用仓库里已经正式锁定并完成验证的 100-tape bank。

## 7. 接手者下一步

1. 完整阅读本文件、[`06-server-ai-handoff.md`](06-server-ai-handoff.md) 和 [`SERVER_RUNBOOK.md`](../nodes/T-05/SERVER_RUNBOOK.md)。
2. 登录服务器后先只读检查两个 worker PID、状态 JSON、事件 ledger、`nvidia-smi` 和当前输出，不要启动重复任务。
3. 若 worker 正常，继续监控；不要人工改队列、预算、seeds、Test bank 或 checkpoint 选择。
4. 若 worker 为 `FAILED`，保留全部失败目录和日志，定位原因；不得覆盖原目录。需要重试时使用新的 `attempt-N` 路径并追加登记。
5. worker 完成后验证：12/12 runs、24 个 policy checkpoints、12/12 evaluations、每次 100 traces、共同 Test manifest、`four-group-ablation.json`。
6. 复核 aggregate 中 `safety.all_shadow_writes_zero == true` 和 `shadow_latency_gates.all_pass == true`；结果为负不等于实验失败。
7. 将本地 worker ledger 中尚未同步的 RUNNING/DONE/FAILED 事件通过 `flock` 追加到中央登记。
8. 生成顶层 SHA-256 inventory，上传不可变 Release，并在独立证据分支/PR 回传紧凑证据。
9. 只有所有正式 Gate 都满足时，才能把 T-05 改为 `passed`。

## 8. 完成后的必交付项

- 服务器环境摘要；
- 12/12 run 状态及所有失败尝试；
- 12/12 fixed-50k evaluation 状态；
- aggregate 结论和负结果；
- 所有安全零写入结论；
- Release URL；
- 证据 PR URL；
- 任何仍存在的限制。

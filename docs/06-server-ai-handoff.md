# T-05 服务器训练：AI 接力执行说明

本文档供另一名 AI/工程师在 CUDA 服务器上直接接管 T-05。执行者应先完整阅读本文档，再阅读 [`SERVER_RUNBOOK.md`](../nodes/T-05/SERVER_RUNBOOK.md) 和冻结配置 [`server-training-config.json`](../nodes/T-05/server-training-config.json)。

## 0. 当前真实状态

截至 2026-09-03：

- T-00～T-04 已通过并有代码、配置、checkpoint、指标和 Release 证据；
- T-05 adapter、只读 Shadow、latent sidecar、旧 GPPO 无损回退、服务器 runner/evaluator/aggregator 已实现；
- 本地 21 个接口/安全 Gates 和 44 项测试通过；
- 正式 T-05 训练为 **0/12 runs**，不是“训练中”，也没有可恢复的服务器进程；
- `formal_server_ablation_complete=false`；
- T-05 必须保持 `in_progress`，直到本文档的 12 runs、12 次 held-out 评估和聚合全部完成。

当前阻塞仅是没有可达 CUDA 服务器。不要在普通本机用缩小预算代替正式实验。

## 1. 接力任务与不可变边界

接力执行者只负责：

1. 在 CUDA 服务器复现冻结环境；
2. 运行 GPPO、WM-GPPO、EA-noGES-GPPO、EAWM-GPPO 四组 × 三 seeds；
3. 对固定 50k checkpoint 使用同一 100 条 held-out Test tapes 评估；
4. 聚合所有结果，包括负结果和失败记录；
5. 上传不可变 Release，并通过独立分支/PR 回传紧凑证据。

接力执行者不得：

- 修改动作空间、奖励、PPO 超参数、seeds、训练预算、场景循环或 Test tapes；
- 让世界模型选择/提交动作，或修改真实 belief、action mask、graph/action version；
- 使用 Test 结果挑选 checkpoint、seed 或实验组；
- 删除失败 run，或只报告最佳 seed；
- 启动 T-06 imagined rollout，或加入人类偏好奖励；
- 在 12-run 证据不完整时把 T-05 改成 `passed`。

## 2. 冻结身份

```text
执行代码仓库: https://github.com/Battleplus/GPPO-WORLD-9.2
执行代码提交: a4432a9527c73021d605f6960dfcc5b8d3e3b3c6
GPPO 基线仓库: https://github.com/Battleplus/GPPO-8.29
GPPO 基线提交: 2a9bb9f87b9d543df144f4d108ba970c924151f9
T-03 checkpoint Release: t03-eawm-v0.1.0
服务器配置 SHA-256: 8373cb3b8a40d6313a8a58c2560ad9985af82ea23fa0049308382862de73351c
训练 seeds: 1101, 2202, 3303
每 run: 50,000 accepted decisions
checkpoint: 25,000 / 50,000
正式 runs: 4 groups × 3 seeds = 12
```

最新 `main` 用于阅读文档和回传证据；正式执行必须在另一份干净 checkout 中固定到 `a4432a9`。`a4432a9` 到当前 `main` 之间，T-05 核心代码、三个服务器脚本、服务器配置和 T-04 calibration 没有漂移。

## 3. 服务器最低条件

- Linux CUDA 服务器；
- Python 3.10 或 3.11；
- `nvidia-smi` 可用，且 Python 中 `torch.cuda.is_available()` 为 `True`；
- Git、Git LFS（如环境需要）、GitHub CLI `gh`；
- `gh` 至少能读取 Release；上传 Release、推送分支和创建 PR 时需要对应仓库权限；
- 输出目录有足够空间保存 12 runs、24 个 policy checkpoints、1200 条评估 traces、日志和归档。

不要预先声称所需显存、训练时长或吞吐；这些必须由服务器的 `environment.json`、`live_progress.json` 和实际运行记录给出。

## 4. 建立隔离目录

下面以 `/srv/gppo-t05` 为例。可以换路径，但必须在所有命令中保持一致。

```bash
export T05_ROOT=/srv/gppo-t05
export CONTROL_REPO="$T05_ROOT/control"
export RUN_REPO="$T05_ROOT/run-target"
export BASELINE_REPO="$T05_ROOT/GPPO-8.29"
export WORLD_DIR="$T05_ROOT/world-checkpoints"
export BANK_DIR="$T05_ROOT/frozen-bank"
export RUNS_DIR="$T05_ROOT/runs"
export EVAL_DIR="$T05_ROOT/evaluation"
export TARGET_COMMIT=a4432a9527c73021d605f6960dfcc5b8d3e3b3c6
export BASELINE_COMMIT=2a9bb9f87b9d543df144f4d108ba970c924151f9
export CONFIG_SHA=8373cb3b8a40d6313a8a58c2560ad9985af82ea23fa0049308382862de73351c

mkdir -p "$T05_ROOT"
git clone https://github.com/Battleplus/GPPO-WORLD-9.2.git "$CONTROL_REPO"
git -C "$CONTROL_REPO" switch -c t05-server-campaign origin/main

git clone https://github.com/Battleplus/GPPO-WORLD-9.2.git "$RUN_REPO"
git -C "$RUN_REPO" checkout --detach "$TARGET_COMMIT"

git clone https://github.com/Battleplus/GPPO-8.29.git "$BASELINE_REPO"
git -C "$BASELINE_REPO" checkout --detach "$BASELINE_COMMIT"
```

确认两个执行仓库干净且版本完全一致：

```bash
test "$(git -C "$RUN_REPO" rev-parse HEAD)" = "$TARGET_COMMIT"
test -z "$(git -C "$RUN_REPO" status --porcelain)"
test "$(git -C "$BASELINE_REPO" rev-parse HEAD)" = "$BASELINE_COMMIT"
test -z "$(git -C "$BASELINE_REPO" status --porcelain)"
test "$(sha256sum "$RUN_REPO/nodes/T-05/server-training-config.json" | cut -d' ' -f1)" = "$CONFIG_SHA"
```

任何一项失败都必须停下，不得继续训练。

## 5. 建立 Python/CUDA 环境

```bash
python3.11 -m venv "$T05_ROOT/venv"
source "$T05_ROOT/venv/bin/activate"
python -m pip install --upgrade pip
```

基线复现锁定 PyTorch `2.7.1`。先根据服务器驱动安装与 CUDA 匹配的官方 PyTorch 2.7.1 wheel，再安装其余锁定依赖：

```bash
grep -v '^torch==' "$BASELINE_REPO/ppo_allocation/requirements-random-event-lock.txt" > "$T05_ROOT/requirements-no-torch.txt"
python -m pip install -r "$T05_ROOT/requirements-no-torch.txt"
python -m pip install -e "$RUN_REPO[test]"
```

CUDA 预检必须通过：

```bash
nvidia-smi
python -c "import sys, torch; print(sys.version); print(torch.__version__, torch.version.cuda, torch.cuda.is_available(), torch.cuda.get_device_name(0)); assert torch.cuda.is_available()"
```

把 `pip freeze`、Python、PyTorch、CUDA、cuDNN、GPU、driver 和 hostname 保存到 `$T05_ROOT/environment-preflight.txt`。不得在不同 run 之间升级依赖。

## 6. 下载并校验九个世界模型 checkpoint

```bash
mkdir -p "$WORLD_DIR"
gh release download t03-eawm-v0.1.0 \
  --repo Battleplus/GPPO-WORLD-9.2 \
  --dir "$WORLD_DIR" \
  --pattern 'wm_seed*.pt' \
  --pattern 'ea_no_ges_seed*.pt' \
  --pattern 'eawm_hard_seed*.pt'
```

应恰好得到九个 `.pt` 文件。其文件名和 SHA-256 已冻结在 `server-training-config.json`；runner 会在训练前再次逐个校验。执行者还应保存一份外部清单：

```bash
find "$WORLD_DIR" -maxdepth 1 -type f -name '*.pt' -print0 | sort -z | xargs -0 sha256sum > "$T05_ROOT/world-checkpoints.sha256"
test "$(find "$WORLD_DIR" -maxdepth 1 -type f -name '*.pt' | wc -l)" -eq 9
```

## 7. 运行服务器前置门禁

先运行全部测试和真实 checkpoint 的小型接口验证。验证输出必须写到执行仓库外，保持 `RUN_REPO` 干净：

```bash
cd "$RUN_REPO"
python -m pytest -q

mkdir -p "$T05_ROOT/preflight"
python tools/validate_t05_local.py \
  --baseline-root "$BASELINE_REPO" \
  --world-checkpoint "$WORLD_DIR/eawm_hard_seed20260903.pt" \
  --output "$T05_ROOT/preflight/local-interface-validation.json"

test -z "$(git -C "$RUN_REPO" status --porcelain)"
```

预期：44 项测试通过，`all_local_gates_pass=true`，belief/mask/version/environment/action-submission 写入均为 0，legacy/disabled parity 为 bit-exact。若不满足，停止正式训练。

## 8. 生成并冻结唯一 Test bank

```bash
cd "$BASELINE_REPO"
PYTHONPATH="$BASELINE_REPO" python -m ppo_allocation.random_event.experiment protocol-bank \
  --output-dir "$BANK_DIR" \
  --tier preliminary \
  --split test \
  --seed-manifest "$BASELINE_REPO/configs/seed_manifest.json" \
  --protocol "$BASELINE_REPO/configs/random_event_protocol.json" \
  --events-per-tape 5

export TEST_MANIFEST="$BANK_DIR/tapes/preliminary_test_protocol/manifest.json"
test -f "$TEST_MANIFEST"
find "$BANK_DIR" -type f -print0 | sort -z | xargs -0 sha256sum > "$T05_ROOT/frozen-bank.sha256"
```

evaluator 会强制要求 manifest 恰好包含 100 条 tapes。Test bank 只生成一次；12 次评估必须使用同一个文件和同一 SHA-256。

## 9. 运行 12 个正式训练

矩阵固定如下：

| Group | Seeds | 目标 |
|---|---|---|
| GPPO | 1101, 2202, 3303 | 3/3 |
| WM-GPPO | 1101, 2202, 3303 | 3/3 |
| EA-noGES-GPPO | 1101, 2202, 3303 | 3/3 |
| EAWM-GPPO | 1101, 2202, 3303 | 3/3 |

单个 run 的标准命令：

```bash
cd "$RUN_REPO"
export GROUP=EAWM-GPPO
export SEED=1101
export GPU_ID=0
export RUN_DIR="$RUNS_DIR/$GROUP/seed$SEED"

CUDA_VISIBLE_DEVICES="$GPU_ID" python tools/run_t05_server_training.py \
  "$GROUP" "$SEED" "$RUN_DIR" \
  --baseline-root "$BASELINE_REPO" \
  --world-checkpoint-dir "$WORLD_DIR" \
  --expected-target-commit "$TARGET_COMMIT"
```

执行者应遍历四组 × 三 seeds。单 GPU 可顺序运行；多 GPU 可并行，但每个 run 必须有独占输出目录和明确 `CUDA_VISIBLE_DEVICES`。不要让两个进程写同一目录。

每个成功 run 必须满足：

- `run-summary.json.status == "done"`；
- `accepted_decision_steps == 50000`；
- 存在 25k 和 50k 两个 checkpoint；
- `safety-audit.json` 中 belief/mask/version/action submission 写入为 0；
- `sha256-inventory.json` 完整；
- `progress/live_progress.json` 最终为 `done`。

监控时读取各 run 的 `progress/live_progress.json`，不要根据终端是否有输出猜测状态。

失败 run 不得覆盖或删除。保留原目录与日志，使用新的 `attempt-N` 目录重跑，并在最终 `failed-runs.json` 记录原因。runner 会拒绝覆盖非空目录。

## 10. 固定 50k checkpoint 的 12 次评估

禁止评估 25k 后挑选较好 checkpoint。每个 run 只评估 `run-summary.json` 中 step=50000 的 checkpoint，并把其中记录的 SHA-256传给 evaluator。

单次评估示例：

```bash
cd "$RUN_REPO"
export GROUP=EAWM-GPPO
export SEED=1101
export GPU_ID=0
export RUN_DIR="$RUNS_DIR/$GROUP/seed$SEED"
export SUMMARY="$RUN_DIR/run-summary.json"
export CHECKPOINT_REL=$(python -c 'import json,sys; d=json.load(open(sys.argv[1])); print(next(x["path"] for x in d["checkpoints"] if x["step"] == 50000))' "$SUMMARY")
export CHECKPOINT_SHA=$(python -c 'import json,sys; d=json.load(open(sys.argv[1])); print(next(x["sha256"] for x in d["checkpoints"] if x["step"] == 50000))' "$SUMMARY")
export CHECKPOINT="$RUN_DIR/$CHECKPOINT_REL"
export OUTPUT_DIR="$EVAL_DIR/$GROUP/seed$SEED"

CUDA_VISIBLE_DEVICES="$GPU_ID" python tools/evaluate_t05_server_checkpoint.py \
  "$GROUP" "$SEED" "$CHECKPOINT" "$TEST_MANIFEST" "$OUTPUT_DIR" \
  --baseline-root "$BASELINE_REPO" \
  --world-checkpoint-dir "$WORLD_DIR" \
  --expected-target-commit "$TARGET_COMMIT" \
  --expected-checkpoint-sha256 "$CHECKPOINT_SHA"
```

12 个输出目录都必须包含 `evaluation.json`、`trace-index.json` 和 100 条 tape traces。不要重用非空评估目录。

## 11. 聚合，不选择赢家

```bash
cd "$RUN_REPO"
python tools/aggregate_t05_server_results.py \
  "$EVAL_DIR" \
  "$T05_ROOT/four-group-ablation.json" \
  --baseline-root "$BASELINE_REPO" \
  --expected-target-commit "$TARGET_COMMIT" \
  --expected-config-sha256 "$CONFIG_SHA"
```

aggregator 会强制检查：恰好 12 份评估、共同 Test manifest、共同 commit/config/calibration、checkpoint metadata、逐 seed 配对 tape 顺序、Shadow latency schema 和安全零写入。结果为负不等于实验失败；必须如实保存，不能重新挑 seed 或改预算。

聚合成功后还需确认：

- `safety.all_shadow_writes_zero == true`；
- `shadow_latency_gates.all_pass == true`；
- 四组 × 三 seed 的 summary 全部存在；
- paired effects、seed stability、资源和延迟字段完整；
- preflight 的 legacy/disabled bit-exact Gate 仍通过。

## 12. 代码故障处理规则

如果正式运行暴露真实代码缺陷：

1. 立即停止尚未启动的 runs；
2. 不在服务器上留下未提交的临时补丁继续训练；
3. 从 `a4432a9` 建修复分支，提交最小修复和回归测试；
4. 重新运行全部测试和前置门禁；
5. 将新的 commit 作为所有后续 `--expected-target-commit`；
6. 如果任何正式 run 已使用旧 commit，整批 campaign 必须统一重跑，禁止混合 commit；
7. 如果修改服务器配置，先冻结新的 config SHA，整批 campaign 统一重跑；
8. 在 PR 和最终报告中披露原因、旧失败 run 和新 commit。

不得为了让指标更好而修改算法、超参数、数据或验收阈值。

## 13. Release 与 GitHub 回传

建议 Release tag：`t05-gppo-ablation-v0.1.0`。上传前生成顶层 SHA-256 inventory，覆盖：

- 12 个 run manifests、environment、history、progress、25k/50k checkpoints、safety audit、run summary 和内部 inventory；
- 唯一 frozen Test bank manifest 与 inventory；
- 12 个 `evaluation.json`、trace index 和完整 traces；
- `four-group-ablation.json`；
- 环境预检、失败记录和所有归档文件。

若资产较大，可以按 run/评估拆分归档，但不得省略；每个 Release asset 都必须记录字节数、SHA-256 和不可变下载 URL。

在 `$CONTROL_REPO` 的 `t05-server-campaign` 分支提交紧凑证据，至少包括：

```text
nodes/T-05/evidence/server-campaign-manifest.json
nodes/T-05/evidence/checkpoint-manifest.json
nodes/T-05/evidence/four-group-ablation.json
nodes/T-05/evidence/failed-runs.json
nodes/T-05/evidence/server-test-report.md
nodes/T-05/evidence/release-assets.json
```

同时更新：

- `nodes/T-05/README.md`；
- `nodes/status.json`；
- `docs/05-current-progress.md`；
- 根 `README.md` 的能力声明。

只有本文档全部 Gate 满足时，才能把 T-05 改成 `passed`。否则保持 `in_progress` 并准确记录已完成 runs、失败原因和下一阻塞。

最后推送分支并创建 PR，不要绕过审查直接覆盖 `main`：

```bash
git -C "$CONTROL_REPO" status --short
git -C "$CONTROL_REPO" add nodes/T-05 nodes/status.json docs/05-current-progress.md README.md
git -C "$CONTROL_REPO" commit -m "Complete T-05 server ablation evidence"
git -C "$CONTROL_REPO" push -u origin t05-server-campaign
cd "$CONTROL_REPO"
gh pr create --base main --head t05-server-campaign --title "Complete T-05 server ablation evidence" --body-file nodes/T-05/evidence/server-test-report.md
```

向用户返回：服务器环境摘要、12/12 run 状态、12/12 evaluation 状态、aggregate 结论、Release URL、PR URL，以及任何负结果或限制。

## 14. 完成检查表

- [ ] 运行代码固定为一个干净 commit；
- [ ] 基线固定为 `2a9bb9f`；
- [ ] 配置 SHA 与冻结值一致；
- [ ] 九个世界模型 checkpoint SHA 全部匹配；
- [ ] 44 项测试和本地接口 Gates 通过；
- [ ] 唯一 100-tape Test bank 已冻结并生成 inventory；
- [ ] 12/12 runs 达到 50,000 accepted decisions；
- [ ] 24 个 policy checkpoints 与全部日志/安全清单存在；
- [ ] 12/12 固定 50k held-out evaluations 完成；
- [ ] aggregate 包含所有逐 seed、配对、bootstrap、资源与延迟结果；
- [ ] belief/action mask/version/environment/Shadow submission 写入均为 0；
- [ ] disabled/legacy GPPO 回退仍 bit-exact；
- [ ] 失败和负结果完整保留；
- [ ] GitHub Release、证据 commit 和 PR 可访问；
- [ ] 只有上述全部满足时，T-05 才标记 `passed`。

## 15. 可直接交给另一名 AI 的提示词

```text
请克隆 https://github.com/Battleplus/GPPO-WORLD-9.2 ，完整阅读
docs/06-server-ai-handoff.md、nodes/T-05/SERVER_RUNBOOK.md 和
nodes/T-05/server-training-config.json，然后严格执行 T-05 CUDA server campaign。

正式运行代码固定到 a4432a9527c73021d605f6960dfcc5b8d3e3b3c6，GPPO 基线固定到
2a9bb9f87b9d543df144f4d108ba970c924151f9。不得缩小预算、修改 seeds、挑选
Test checkpoint 或删掉负结果。完成 4 groups × 3 seeds × 50k、12 次固定
held-out 评估、聚合、安全零写入审计、Release 和 PR。若无 CUDA、身份/SHA
不匹配或任何 Gate 失败，立即停止并报告真实阻塞，不得把 T-05 标成 passed。
```

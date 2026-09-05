# 三类型 GPPO 基础演示复现手册

本手册锁定已有 GPPO 50k 基础策略。正式 T-05 evaluator 要求 CUDA、冻结源码、干净 worktree 和固定 checkpoint 元数据；不要直接在本 S0 文档提交上冒充正式复现。

## 依赖和资产

- Python 3.10 或 3.11；T-05 冻结配置只允许这两个版本。
- PyTorch、NumPy；完整 baseline 依赖按 `ppo_allocation/requirements-random-event-lock.txt` 安装。
- GPPO-WORLD 运行代码 `69e3be5931deea7371df77d75fb14f2f5bdeab72` 的独立 checkout。
- GPPO-8.29 `2a9bb9f87b9d543df144f4d108ba970c924151f9` 的独立 checkout。
- T-05 Release 中 `t05-run-artifacts.tar.gz`、`t05-evaluation-artifacts.tar.gz`、`test-bank-manifest.json`、`server-training-config.json`，以及 T-03 Release 的世界模型资产目录（纯 GPPO 评估仍由 evaluator 要求该目录参数，但不会加载其中模型）。

选定策略 archive member：`runs/GPPO/seed1101-attempt-2/models/gppo_seed1101_step50000.pt`，SHA-256 为 `8c11eabbba79c3a0adc1785e84c5b793fecc4d3b9299630a2f18a5d8cfa253b1`。

## 准备命令（未在 S0 端到端执行）

```bash
git clone https://github.com/Battleplus/GPPO-WORLD-9.2.git gppo-world-t05
git -C gppo-world-t05 checkout --detach 69e3be5931deea7371df77d75fb14f2f5bdeab72
git clone https://github.com/Battleplus/GPPO-8.29.git gppo-829-baseline
git -C gppo-829-baseline checkout --detach 2a9bb9f87b9d543df144f4d108ba970c924151f9
python3.10 -m venv .venv-t05
source .venv-t05/bin/activate
python -m pip install -r gppo-829-baseline/ppo_allocation/requirements-random-event-lock.txt
python -m pip install -e gppo-world-t05
```

下载 T-05 Release 资产后校验 `release-assets-sha256.txt`，解开两个 tar.gz，并从运行资产中取出选定 checkpoint。所有输出目录必须新建且为空；evaluator 会拒绝覆盖非空目录。

## 完整 held-out 评估命令（未在 S0 执行）

```bash
cd gppo-world-t05
python tools/evaluate_t05_server_checkpoint.py \
  GPPO 1101 \
  /ABS/t05-runs/runs/GPPO/seed1101-attempt-2/models/gppo_seed1101_step50000.pt \
  /ABS/test-bank/manifest.json \
  /ABS/output/GPPO-seed1101 \
  --baseline-root /ABS/gppo-829-baseline \
  --world-checkpoint-dir /ABS/t03-world-models \
  --expected-target-commit 69e3be5931deea7371df77d75fb14f2f5bdeab72 \
  --expected-checkpoint-sha256 8c11eabbba79c3a0adc1785e84c5b793fecc4d3b9299630a2f18a5d8cfa253b1 \
  --config nodes/T-05/server-training-config.json
```

运行前检查：`git status --porcelain` 在两个 checkout 均为空；`git rev-parse HEAD` 分别匹配上述提交；`nvidia-smi` 可用；test manifest SHA-256 为 `f295bc42ba932ed192162f231670de3865dedae7f2d737331576b90f2cf88bf5`；配置 SHA-256 为 `973dc586fb0bac268ab753c180b8a19cfe0e01430b3bd9251c91118af4871225`。

## S0 实际执行范围

S0 从已经下载并校验的 T-05 资产解出 checkpoint，核对 SHA-256，并在本机 Python 3.13 / CPU PyTorch 2.13 上成功加载模型及元数据。没有安装 baseline 完整依赖 `gymnasium`，没有 CUDA，因此没有运行 episode、延迟测量或 100-tape 评估。结果见 [checkpoint-load.json](checkpoint-load.json) 和 [artifact-verification.json](artifact-verification.json)。

## 延迟口径

T-05 `inference_latency_ms` 包围一次策略选动作调用；世界模型组还包含 adapter/shadow 相关路径。S2 比较普通 PPO、GPPO 和候选五类型/压缩版本时，必须固定硬件、线程、batch=1、图实体数、动作空间、预热、同步和采样 tape，并分别报告纯前向及端到端 P50/P95/P99。现有 3.75–4.22 ms 均值不能证明会议“GPPO/GPO 比 PPO 慢 3～4 倍”。

# T-05 server/GPU runbook

This runbook is executable only on a reachable CUDA server. Local execution is limited to `tools/validate_t05_local.py`.

## 1. Freeze inputs

Clone both repositories, check out the exact target commit recorded at launch and baseline `2a9bb9f87b9d543df144f4d108ba970c924151f9`, require both worktrees clean, and use Python 3.10 or 3.11. The run scripts repeat these checks and refuse drift.

Download the T-03 Release checkpoints into one immutable directory:

```bash
gh release download t03-eawm-v0.1.0 \
  --repo Battleplus/GPPO-WORLD-9.2 \
  --dir /srv/gppo-t05/world-checkpoints \
  --pattern 'wm_seed*.pt' \
  --pattern 'ea_no_ges_seed*.pt' \
  --pattern 'eawm_hard_seed*.pt'
```

The nine expected hashes are frozen in `server-training-config.json`; a mismatch aborts before training.

Generate the committed preliminary held-out Test bank once from the baseline root:

```bash
python -m ppo_allocation.random_event.experiment protocol-bank \
  --output-dir /srv/gppo-t05/frozen-bank \
  --tier preliminary \
  --split test \
  --seed-manifest /path/to/GPPO-8.29/configs/seed_manifest.json \
  --protocol /path/to/GPPO-8.29/configs/random_event_protocol.json \
  --events-per-tape 5
```

Freeze and record SHA-256 for `/srv/gppo-t05/frozen-bank/tapes/preliminary_test_protocol/manifest.json` and every tape. The manifest must contain exactly 100 tapes.

## 2. Train 12 independent runs

For every Cartesian pair below, use a fresh output directory and assign a GPU with `CUDA_VISIBLE_DEVICES`:

```text
groups = GPPO, WM-GPPO, EA-noGES-GPPO, EAWM-GPPO
seeds  = 1101, 2202, 3303
```

Example:

```bash
CUDA_VISIBLE_DEVICES=0 python tools/run_t05_server_training.py \
  EAWM-GPPO 1101 /srv/gppo-t05/runs/EAWM-GPPO/seed1101 \
  --baseline-root /path/to/GPPO-8.29 \
  --world-checkpoint-dir /srv/gppo-t05/world-checkpoints \
  --expected-target-commit TARGET_COMMIT
```

The runner fixes 50,000 accepted decisions, checkpoint steps 25,000/50,000, the baseline PPO hyperparameters, seed namespace and train mode cycle. It refuses CPU-only execution. The GPU runs GPPO; immutable T-04 Shadow snapshots and WM inference stay on CPU to preserve the passed read-only contract. This split is recorded in the environment manifest.

Do not restart into an existing run directory. A failed run is retained and a new run receives a new directory and failure record.

## 3. Evaluate the fixed 50k checkpoint

Do not use Test results for checkpoint selection. Pass the exact checkpoint SHA from `run-summary.json`:

```bash
CUDA_VISIBLE_DEVICES=0 python tools/evaluate_t05_server_checkpoint.py \
  EAWM-GPPO 1101 \
  /srv/gppo-t05/runs/EAWM-GPPO/seed1101/models/eawm_gppo_seed1101_step50000.pt \
  /srv/gppo-t05/frozen-bank/tapes/preliminary_test_protocol/manifest.json \
  /srv/gppo-t05/evaluation/EAWM-GPPO/seed1101 \
  --baseline-root /path/to/GPPO-8.29 \
  --world-checkpoint-dir /srv/gppo-t05/world-checkpoints \
  --expected-target-commit TARGET_COMMIT \
  --expected-checkpoint-sha256 CHECKPOINT_SHA256
```

Repeat for all 12 fixed checkpoints, then aggregate without selecting a group:

```bash
python tools/aggregate_t05_server_results.py \
  /srv/gppo-t05/evaluation \
  /srv/gppo-t05/four-group-ablation.json \
  --baseline-root /path/to/GPPO-8.29 \
  --expected-target-commit TARGET_COMMIT \
  --expected-config-sha256 SERVER_TRAINING_CONFIG_SHA256
```

## 4. Release and node evidence

Before upload, generate a top-level SHA-256 inventory containing every run manifest, environment file, progress/history log, checkpoint, safety audit, held-out result and trace index. Upload immutable assets to a `t05-*` GitHub Release. Commit only compact manifests, metrics, failure records, test report and Release URLs under `nodes/T-05/evidence/`.

T-05 may become `passed` only when:

- all 12 runs reached exactly 50,000 accepted decisions;
- every required checkpoint/log/config/seed/commit/hash is present;
- all 12 held-out evaluations use the same 100-tape manifest;
- belief/mask/version/environment mutation and Shadow action-submission counters are zero;
- zero/off and legacy checkpoint parity remain bit-exact;
- the aggregate contains all per-seed results, dispersion, paired effects and bootstrap intervals, including negative/failed results.

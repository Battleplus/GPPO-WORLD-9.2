# M-10-R 复现运行手册

## 固定输入

- 分支：`execute-r02-20260905`
- 修正源码提交：本地 `9da596c`；服务器非强制同步提交：`db0c74a6633c6c5aa7c32671073824478f4fff15`
- Python：服务器 `/home/user1/m10-test-venv/bin/python`
- 依赖补充路径：`/home/user1/s1-gppo-venv/lib/python3.10/site-packages`
- 设备：指定服务器 CUDA；本轮未停止既有 TensorBoard。

## 验收和 pilot

```text
PYTHONPATH=/home/user1/m10-test-venv/lib/python3.10/site-packages:/home/user1/s1-gppo-venv/lib/python3.10/site-packages:/path/to/repo \
/home/user1/m10-test-venv/bin/python tools/run_m10_causal_acceptance.py --output causal-acceptance.json
```

pilot 使用 `--mode pilot --device cuda --steps 128 --world-episodes 8 --world-epochs 5 --trigger-max-interval 3`，仅验证真实梯度、吞吐和协议，不用于正式结论。

## 正式矩阵

```text
PYTHONPATH=/home/user1/m10-test-venv/lib/python3.10/site-packages:/home/user1/s1-gppo-venv/lib/python3.10/site-packages:/path/to/repo \
/home/user1/m10-test-venv/bin/python tools/run_m10_training.py \
  --mode matrix --output formal --device cuda --steps 2048 \
  --world-episodes 64 --world-epochs 30 --trigger-max-interval 3
```

脚本固定 train/validation/test/OOD tape，使用 seed 1101、2203、3307；世界模型阈值只从 validation rows 选择，正式结果必须存在 `run-complete.json`、6×3 checkpoint、逐 seed records、`world-model.json` 和 latency 字段。禁止用测试集调阈值、择优 checkpoint 或把 `replans` 字段解释为事件触发次数。

## 复核命令与交付

```text
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=/path/to/repo \
python -m pytest -q --basetemp /isolated/tmp
python tools/run_m10_causal_acceptance.py --output causal-acceptance.json
sha256sum m10r-source-20260907-v2.tar m10r-training-artifacts-20260907-clean.tar.gz
```

下载前在服务器核对 SHA-256，下载后独立展开并再次核对源码、matrix-results、world-model 和 run-complete。新 Release 必须使用独立 tag/资产；不得改写 `m10-meeting-research-v1-20260907`、main 或 force push。

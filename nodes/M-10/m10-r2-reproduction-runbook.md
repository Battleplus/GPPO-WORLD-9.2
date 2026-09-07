# M-10-R2 复现说明

## 代码与环境

分支：`execute-r02-20260905`。R2 远端提交：`b73bcbc3ce78cdc17cc5e365fa259a45e309ec2e`。服务器使用 `/home/user1/m10-test-venv/bin/python`，并通过 `PYTHONPATH` 加入该环境的 supplemental site-packages 和源码根目录。

## 正确性测试

```text
export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
export PYTHONPATH=/home/user1/m10-test-venv/lib/python3.10/site-packages:/home/user1/s1-gppo-venv/lib/python3.10/site-packages:$PWD
/home/user1/m10-test-venv/bin/python -m pytest -q --basetemp <new-run>/pytest-tmp
```

服务器 R2 结果：153 passed、7 skipped；skip 为缺少 pinned GPPO baseline。

## pilot

```text
/home/user1/m10-test-venv/bin/python tools/run_m10_training.py \
  --mode pilot --output <new-run>/pilot-v3 --device cuda --steps 128 \
  --world-episodes 8 --world-epochs 5 --seeds 1101 --trigger-max-interval 3
```

pilot 不用于正式收益结论；需核对 triggered 的 actor_decisions、continuation_steps、replan_reasons 和 benchmark。

## 正式矩阵

```text
/home/user1/m10-test-venv/bin/python tools/run_m10_training.py \
  --mode matrix --output <new-run>/formal-v1 --device cuda --steps 2048 \
  --world-episodes 64 --world-epochs 30 --seeds 1101,2203,3307 \
  --trigger-max-interval 3
```

每组必须检查 2048 environment_steps、8 rollout_updates、4 update_epochs、32 optimizer_updates。必须保留 test/OOD tape、优化器状态、逐 seed 记录和校准阈值；不能以最佳 seed 或最佳 checkpoint 替代完整矩阵。

## 归档核对

先下载服务器 `formal-v1`、pilot 和源码包，逐项执行 SHA-256，再创建 R2 独立 Release。不要修改 M-09、M-10、M-10-R 旧 Release，不 force push，不把密码写入脚本、日志或归档。

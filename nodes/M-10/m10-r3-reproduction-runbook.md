# M-10-R3 复现手册

## 代码与环境

- 分支：`execute-r02-20260905`
- R3 源码提交：`b3a0b6d`（远端安全更新头 `935ee5e4586cad79d2a72c4da864ce36a7f77893`）
- 服务器：`172.17.27.173:user1`
- Python：服务器专用 `/home/user1/m10-test-venv/bin/python`
- 依赖路径：`/home/user1/m10-test-venv/lib/python3.10/site-packages:/home/user1/s1-gppo-venv/lib/python3.10/site-packages`
- 训练位置：指定服务器专用目录，未修改共享环境，未停止已有 TensorBoard。

## 服务器测试

在源码目录执行：

```text
export PYTHONPATH=/home/user1/m10-test-venv/lib/python3.10/site-packages:/home/user1/s1-gppo-venv/lib/python3.10/site-packages:$PWD
/home/user1/m10-test-venv/bin/python -m pytest -q -p no:cacheprovider
```

R3 针对性测试为 11 passed；服务器全套为 155 passed、7 skipped。skip 是既有 pinned GPPO baseline 缺失，不是通过。

## 运行标识与主要命令

固定 R2 world checkpoint：`/home/user1/m10-runs/20260907-r2-correctness-v1/formal-v1/world-model.pt`。

预测审计：

```text
/home/user1/m10-test-venv/bin/python tools/run_m10_r3.py --mode prediction --output /home/user1/m10-runs/20260907-r3-prediction-trigger-cost-v1/prediction-cuda --world-checkpoint /home/user1/m10-runs/20260907-r2-correctness-v1/formal-v1/world-model.pt --device cuda
```

同 checkpoint 触发对照：

```text
/home/user1/m10-test-venv/bin/python tools/run_m10_r3.py --mode trigger --output /home/user1/m10-runs/20260907-r3-prediction-trigger-cost-v1/trigger-cuda --world-checkpoint /home/user1/m10-runs/20260907-r2-correctness-v1/formal-v1/world-model.pt --policy-checkpoint /home/user1/m10-runs/20260907-r2-correctness-v1/formal-v1/checkpoints/graph-5-world/seed-1101.pt --device cuda --threshold 0.1 --max-replan-interval 3
/home/user1/m10-test-venv/bin/python tools/run_m10_r3.py --mode trigger --output /home/user1/m10-runs/20260907-r3-prediction-trigger-cost-v1/trigger-cpu-v2 --world-checkpoint /home/user1/m10-runs/20260907-r2-correctness-v1/formal-v1/world-model.pt --policy-checkpoint /home/user1/m10-runs/20260907-r2-correctness-v1/formal-v1/checkpoints/graph-5-world/seed-1101.pt --device cpu --threshold 0.1 --max-replan-interval 3
```

学习阶梯：

```text
/home/user1/m10-test-venv/bin/python tools/run_m10_r3.py --mode ladder --output /home/user1/m10-runs/20260907-r3-prediction-trigger-cost-v1/learning-ladder-cuda --world-checkpoint /home/user1/m10-runs/20260907-r2-correctness-v1/formal-v1/world-model.pt --device cuda --threshold 0.1 --budgets 2048,4096,8192 --seed 1101
```

正式公平矩阵：

```text
/home/user1/m10-test-venv/bin/python tools/run_m10_r3.py --mode formal --output /home/user1/m10-runs/20260907-r3-prediction-trigger-cost-v1/formal-matrix-cuda --world-checkpoint /home/user1/m10-runs/20260907-r2-correctness-v1/formal-v1/world-model.pt --device cuda --threshold 0.1 --formal-steps 8192 --seeds 1101,2203,3307
```

## 数据与解释

训练、validation、历史 test、OOD 和 final-test tape 在 runner 中使用不同 seed 地址。历史 test 是回归集；final-test base seed `91001` 在本轮选择后冻结并只用于最终评估。事件窗口为 `env.step` 后的下一个环境决策间隔，事件位为 damage/disconnect/reconnect/reserved_event_3。事件和 done 指标使用 train baseline，最终 tape 不参与选择。

## 制品核验

R3 Release 归档必须包含：源码 tar、测试摘要、prediction-audit、trigger comparison、learning ladder、formal matrix、逐 seed checkpoint、optimizer/recovery state、配置、tapes、日志、SHA-256 manifest 和本报告。下载完成后先核验本地 SHA-256，再创建独立 R3 Release；不覆盖 main、M-09、M-10、M-10-R 或 M-10-R2 Release。

# M-10 弱通信阶段复现手册

训练服务器：`172.17.27.173`，专用环境：`/home/user1/s1-gppo-venv`。凭据不属于手册、源码或日志。

## 运行顺序

1. 先运行合同审计：

   `/home/user1/s1-gppo-venv/bin/python tools/run_m10_weak_comm_audit.py`

   本阶段服务器结果写入 `formal/weak-comm-contract-audit-r2.txt`，为 10/10；服务器未安装 pytest，不能把它称为 pytest 全套。

2. pilot（历史实际命令）：

   `/home/user1/s1-gppo-venv/bin/python tools/run_m10_weak_comm.py --mode pilot --output /home/user1/m10-runs/20260907-weak-comm-v1/pilot --device cuda --steps 2048 --rollout-steps 256 --world-epochs 30 --level composite`

3. formal（历史实际命令，最终测试 tape 在选择后使用）：

   `/home/user1/s1-gppo-venv/bin/python tools/run_m10_weak_comm.py --mode formal --output /home/user1/m10-runs/20260907-weak-comm-v1/formal --device cuda --formal-steps 12288 --rollout-steps 256 --level composite --world-checkpoint /home/user1/m10-runs/20260907-weak-comm-v1/pilot/world-model.pt --world-policy-checkpoint /home/user1/m10-runs/20260907-weak-comm-v1/pilot/pilot/checkpoints/B-graph5-world.pt --threshold 0.1 --max-wait 3 --seeds 1101,2203,3307`

4. 只读详细成本与恢复审计：

   `/home/user1/s1-gppo-venv/bin/python tools/evaluate_m10_weak_comm_details.py --tapes .../formal/tapes.json --world .../pilot/world-model.pt --policy-a .../formal/checkpoints/A-graph5-base/seed-1101.pt --policy-b .../formal/checkpoints/B-graph5-world/seed-1101.pt --policy-c .../formal/checkpoints/C-graph5-triggered/seed-1101.pt --output .../formal/detailed-eval.json --device cuda --threshold 0.1 --max-wait 3`

正式训练的每个 seed 是 12,288 environment steps、48 rollout records、每个 record 4 optimizer epochs，故 192 次实际参数更新。不要使用 final-test 重新选择 seed、checkpoint 或阈值。

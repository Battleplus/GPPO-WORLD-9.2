# M-10 NOOP/action-capacity 诊断制品索引

本轮是诊断与可行性验收，不含新增训练。服务器目录：

`/home/user1/m10-runs/20260907-noop-capacity-diagnostic-v1`

| 制品 | 说明 |
|---|---|
| `nodes/M-10/m10-noop-capacity-feasibility-diagnostic.md` | 诊断报告、回报分解、动作容量、补训决策 |
| `tools/diagnose_m10_noop_capacity.py` | 无训练诊断工具；可运行全 NOOP、合法规则、A/B/C 检查点、容量 probe 和必要可行性检查 |
| `noop-capacity-server-v3.json` | 指定服务器 `s1-gppo-venv` 最终复跑 JSON，含逐 episode/逐步 trace、checkpoint 记账和容量 probe |
| `noop-capacity-local.json` | 隔离工作区本地同 tape 复核副本 |

服务器最终 JSON：`noop-capacity-final-with-components-v3-20260907.json`；下载前后 SHA-256 均为：

`a87622c93bf12ccb7f095b4da103c6c20a3eb79a8470c1e45d7bc2181a4bebb3`

运行条件：服务器 `172.17.27.173`，专用目录，既有 `s1-gppo-venv`，CUDA；未启动训练。命令：

```text
/home/user1/s1-gppo-venv/bin/python source/tools/diagnose_m10_noop_capacity.py \
  --tapes /home/user1/m10-runs/20260907-weak-comm-v1/formal/tapes.json \
  --world /home/user1/m10-runs/20260907-weak-comm-v1/pilot/world-model.pt \
  --policy-root /home/user1/m10-runs/20260907-weak-comm-v1/formal/formal/checkpoints \
  --device cuda --max-episodes 16 \
  --output noop-capacity-final-with-components-v3-20260907.json
```

相关测试：本地 M-10 弱通信/诊断针对性测试 `9 passed`；诊断工具 `py_compile` 通过。服务器没有 pytest，服务器结果是直接合同审计/诊断运行，不能写成服务器 pytest 全套通过。

历史 Release、旧训练制品、失败轨迹和负结果均保持不变。

# 弱通信可用性诊断归档索引

本索引对应 M-10 弱通信可用性诊断，不重复上传旧训练归档，不修改历史 Release。

| 项目 | 位置/说明 |
|---|---|
| 服务器运行根 | `/home/user1/m10-runs/20260907-weak-comm-diagnostic-v1` |
| 诊断程序 | `tools/diagnose_m10_weak_comm.py`；无训练、合法调度器与冻结失败 tape 链追踪 |
| 服务器诊断 JSON | `diagnostic.json`；SHA-256 `2b068e9975823dafcba8c01cd9f83f12ea5850a0f77635f1d8974221824fec20`；202,216,260 bytes |
| 服务器合同审计 | `contract-audit-current.txt`；SHA-256 `6ee1dc976a3352adb69d62ce1300816e418eb53504d050b204aaeb3e84518b70`；11 项直连测试 |
| 独立诊断 Release | [m10-weak-comm-availability-diagnostic-v1-20260907](https://github.com/Battleplus/GPPO-WORLD-9.2/releases/tag/m10-weak-comm-availability-diagnostic-v1-20260907)；资产 SHA-256 `ffb4e453ea0c28567d06b52b7d1c70ff4b1662c6ea6989f63c8ffc0d31598cea`；8,349,041 bytes；API digest 与本地下载前校验一致 |
| 源码修正 | `gppo_world/telemetry.py`、`gppo_world/m10_environment.py`：稳定 message_id、delivery ordinal、measured/received 时间审计；不改变策略输入或执行门禁 |
| 新回归 | `tests/test_m10_weak_communication.py`、`tests/test_m10_weak_comm_diagnostic.py`；本地受控 basetemp 全套 `171 passed`，服务器无 pytest，直连诊断 `2 passed` |
| 诊断报告 | `nodes/M-10/m10-weak-communication-availability-diagnostic.md` |
| 输入 tape | 复用既有弱通信 Release 的 `formal/tapes.json`；不重选模型/阈值，不新增训练 |
| 历史制品 | M-09/M-10/M-10-R/R2/R3 和 `m10-weak-comm-gppo-world-v1-20260907` 保持原位置和原 SHA |

服务器文件先下载到本地 `.codex-final-acceptance/` 并复核上述 SHA-256；物理网络字节量未测量，诊断只保留逐消息审计字段和此前明确标注的 JSON 序列化代理。

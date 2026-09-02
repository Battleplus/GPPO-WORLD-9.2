# T-00 合同与适配测试

- 被测提交：`22487f93740ddd1ef428bf0bd7c4f45f7cee27f7`
- 日期：2026-09-02

## 本仓库合同测试

```powershell
python -m pytest -q
```

结果：`15 passed in 2.62s`。

覆盖：

- 三类节点和 16 个候选边 + NOOP；
- graph snapshot 与源 tensor 分离；
- `received_at > decision_time` 拒绝；
- 嵌套 truth-only/future/oracle 字段拒绝；
- proposal 与 executed action 分离；
- 非法动作和 stale graph version 拒绝；
- model input 不包含 `graph_tp1/reward/continuation`；
- random legal、greedy、GPPO 共用同一 recorder；
- 同一 transition 产生 byte-identical JSONL 与 SHA-256。

## 真实 GPPO 适配验证

```powershell
python tools\validate_gppo_baseline.py E:\Z博士\9.2日\GPPO-8.29-baseline
```

结果见 [`gppo-adapter-validation.json`](gppo-adapter-validation.json)：节点形状、17 动作合同、NOOP 索引、合法动作前向和 critic finite 检查全部通过。

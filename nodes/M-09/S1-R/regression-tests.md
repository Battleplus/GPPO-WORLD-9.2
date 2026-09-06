# S1-R 回归测试

本地执行：

```text
PYTHONPATH=. PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/test_s1_r_contracts.py
```

7 项通过，覆盖：

- 正常结束但任务未完成；
- deadline 逾期与普通 timeout 区分；
- stale 重试更换 UAV 并只扣新端点；
- 低能量重试重新检查；
- 重复提交不重复扣费；
- 首次分配不计重分配；
- 低置信度 payload 未确认不得通过。

服务器执行工具同时保留完整 60 条 trace 和四条执行层探针结果。

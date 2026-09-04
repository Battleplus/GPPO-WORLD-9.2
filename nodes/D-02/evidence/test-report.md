# D-02 验证记录

2026-09-04：`python -m pytest -q`，60 passed。

新增 8 项探针测试覆盖正常使用、episode reset、OOD、高不确定度、stale、timeout 原因记录，模型状态/RNG/输出不变、每次只读一次 context，以及拒绝 train 模式和异常后清理 hooks。

真实开发复放：9 个固定模型 × 12 条开发带 × probe on/off = 216 episodes；108 对通过。

独立验证器 `tools/verify_d02_evidence.py` 重新核对 270 个原始清单文件、216 条完整 trace、623 条探针记录，结果 PASS；不仅依赖实验程序输出的布尔字段。

没有在本次自然样本中观察到 OOD/timeout/stale，不把单元测试的原因记录验证当成新的环境故障注入实验。

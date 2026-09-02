# GPPO 基线验证记录

- 源码：`Battleplus/GPPO-8.29@2a9bb9f87b9d543df144f4d108ba970c924151f9`
- 环境：Windows，Python 3.14.4，PyTorch 2.13.0+cpu，NumPy 2.5.0
- 日期：2026-09-02

## 执行命令

从 `ppo_allocation` 目录执行：

```powershell
$env:PYTHONPATH=(Get-Location).Path
python -m unittest `
  tests_random_event.test_random_event_core `
  tests_random_event.test_random_event_training `
  tests_random_event.test_concurrency_invariants `
  tests_random_event.test_event_runtime_integration
```

## 结果

```text
Ran 50 tests in 3.169s
OK
```

覆盖了图/动作合同、环境事件、GraphActorCritic forward/save/load、最小 PPO train/save/load、graph/action version、ACK、lease、fencing、确定性事件回放和 RuntimeBridge 集成。

## 限制

源仓库 checkpoint index 登记了 12 个 25k/50k 模型，但 Git 跟踪文件中没有 `.pt/.pth/.ckpt` 二进制。因此当前只确认清单存在，**没有**宣称这些历史 checkpoint 已在 T-00 加载验证。最小训练测试生成的临时 checkpoint 已由源测试完成 roundtrip。

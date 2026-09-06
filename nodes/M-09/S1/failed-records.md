# S1 失败与阻碍记录

## S1-A-001：冻结 baseline 导入失败

- 时间：2026-09-06（服务器只读核查）
- 主机：`172.17.27.173`
- 命令：`/home/user1/anaconda3/envs/dporl/bin/python tools/validate_gppo_baseline.py <GPPO-8.29>`
- 结果：失败，Python `3.9.20` 不接受冻结源码中的 `@dataclass(slots=True)`，错误为
  `TypeError: dataclass() got an unexpected keyword argument 'slots'`。
- 影响：没有创建 episode、策略轨迹或验收结果。

## S1-A-002：替代 Python 3.10 环境不具备复现依赖

- `/usr/bin/python3.10`、DIPO2 和 harl 环境均缺少 `gymnasium`。
- 这些环境从用户 site 导入 Torch 时出现 `libcusparse.so.12` 与 `libnvJitLink.so.12`
  符号版本不匹配。
- 未修改这些环境；仅在 `user1` 私有路径建立隔离环境尝试解决。

## 处理决定

在没有成功导入冻结环境并通过最小轨迹之前，不运行 60 条验收、不训练、不生成通过结论。

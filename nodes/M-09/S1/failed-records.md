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

## 恢复记录

在 `user1` 私有路径 `/home/user1/s1-gppo-venv` 建立 Python 3.10.12 隔离环境，安装
Torch 2.2.2+cu121、Gymnasium 0.29.1 和 NumPy 1.24.4。冻结 baseline 合同验证和
100-tape GPPO 评估随后成功；该环境没有改动 `dporl` 或其他共享环境。

## 处理决定

先完成隔离环境复现和基础轨迹，再运行固定 60 条；训练仍不在 S1 范围内。

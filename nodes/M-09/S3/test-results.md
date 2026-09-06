# S3 测试结果

## 本地

- `python -m pytest -q`：`98 passed`；首次默认临时目录因 Windows 权限失败的 7 个 setup error 已通过工作区隔离临时目录复跑消除；没有把首次环境错误写成代码失败。
- `git diff --check`：通过。
- S3 JSON 产物解析：通过。
- 入口静态核查：`tools/run_s1_r2_acceptance.py` 的模型证据、动作和 stale retry 均经 `torch.inference_mode()`。

## 服务器新鲜冒烟

- 主机：`172.17.27.173`，运行目录：`/home/user1/s3-runs/20260906-a-candidate`；
- 命令退出码：0；标准错误字节数：0；
- tape：6 类 × 10 = 60；
- 每类 `episode_ended=10`、`task_completed=10`、`scenario_assertion_failures=0`；
- future-input、约束、非法有效动作、采集器安全违规：全部 0；
- energy_insufficient：10 次能量拒绝、10 次回退；
- communication_interrupt/composite_three_factor：各 10 次 stale 拒绝；
- confirmation fixture：payload confidence 0.55 被消费；不足证据为 SUSPECTED；足够来源为 CONFIRMED；过期为 EXPIRED；矛盾为 FALSE_ALARM。

服务器没有启动训练进程，也没有停止已有 TensorBoard 或无关进程。

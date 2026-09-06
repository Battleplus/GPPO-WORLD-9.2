# S3 冻结候选复现手册

本手册只复现冻结的三类型候选，不训练、不选择 checkpoint、不启动 S4。完整模型来自 S1-R2/S2 已核验资产；baseline 依赖使用独立 checkout。

## 服务器复现

```bash
source /home/user1/s1-gppo-venv/bin/activate
RUN=/home/user1/s3-runs/<new-empty-run>
python tools/run_s1_r2_acceptance.py \
  /home/user1/s2-runs/20260906-v1/optimized-baseline \
  /home/user1/s2-runs/20260906-v1/checkpoint.pt \
  "$RUN/output" > "$RUN/stdout.log" 2> "$RUN/stderr.log"
```

预期：退出码 0；六类场景共 60 条 tape；每条有明确结束；非法有效动作、future-input、约束和采集器安全违规为 0；通信异常与能量不足的拒绝/回退保留在 trace 中。

入口在 `_model_evidence`、`_policy_action` 和 stale retry 的模型调用处使用 `torch.inference_mode()`。它只改变推理上下文，不改变 checkpoint、输入、动作空间或执行层规则。

## 资产核验

- checkpoint：`gppo_seed1101_step50000.pt`，SHA-256 `8c11eabbba79c3a0adc1785e84c5b793fecc4d3b9299630a2f18a5d8cfa253b1`；
- GPPO-8.29 frozen commit：`2a9bb9f87b9d543df144f4d108ba970c924151f9`；
- S1-R2 patch：`f53efbf95db49ca826b7902b2577217e378d2d96`；
- S2 inference patch：`8613b8c9999b950495813373adb1efa8954121876820e5814cbf6c778a4f2e66`；
- T-05 配置：`973dc586fb0bac268ab753c180b8a19cfe0e01430b3bd9251c91118af4871225`。

原 60 条工程验收与 S3 新鲜冒烟分开统计；两者都不是普通 PPO 或五类型的公平 Test。

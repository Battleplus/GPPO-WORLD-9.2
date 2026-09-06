# 3-5 分钟演示脚本

以下命令是实际使用过的入口的通用化写法；把 `<delivery>` 替换为新解包目录，不使用开发目录或隐式环境变量。

## 0:00-0:30：声明入口

“今天交付两个入口。A 是默认纯 GPPO，Shadow 只读、可关闭；B 是历史 EAWM adapter 复现，不拿来替代 A，也不宣称增益。”

## 0:30-1:30：A 正常和扰动

```text
source <venv>/bin/activate
python <delivery>/tools/run_s5_minimal_reproduction.py \
  --baseline-root <frozen-baseline> \
  --checkpoint <A-policy.pt> \
  --world-checkpoint <world.pt> \
  --calibration <calibration.json> \
  --source-archive <source-archive.tar.gz> \
  --output <new-run>/a-minimal
```

指向输出中的 `reproduction-summary.json`：5 个代表场景、OFF/ON 5/5 签名相等，policy/world unchanged 为 true。强调 energy/damage 是执行层门禁/回退演示，不是说策略通过训练学会了电量规划。

## 1:30-2:30：Shadow 和回退

展示 `fault-injection-results.json` 中：`exception`、`stale_before`、`stale_after`、`timeout`、`ood` 都返回 zero latent；`synthetic_ood.input_ood_score=269.0106024867358`。说明 timeout 是推理调用完成后的 fail-closed gate，不是硬取消；OOD 是合成 feature shift。

## 2:30-3:30：B 历史 adapter 消费

```text
python <target-69e3be5>/tools/evaluate_t05_server_checkpoint.py \
  EAWM-GPPO 1101 <B-policy.pt> <held-out-manifest> <new-run>/b-eawm \
  --baseline-root <frozen-baseline> \
  --world-checkpoint-dir <world-checkpoint-dir> \
  --expected-target-commit 69e3be5931deea7371df77d75fb14f2f5bdeab72 \
  --expected-checkpoint-sha256 bc4e5e9cc1741892ced68f6166845d6c0c5e63452d852c928354669156e1a1bd
```

指向 `evaluation.json` 和逐 decision trace：100 tapes / 635 decisions；487 adapter used；577 valid / 58 fallback；安全计数全零。最后补一句：这只证明历史接口确实消费了匹配 context，不证明 WM 提升了真实回报。

## 3:30-4:30：冻结与下一步

展示 Release 的 SHA-256 与 `汇报.pdf`。结论：“当前可交付的是三类型基础系统、修复后的因果/低置信度合同、延迟优化、只读 Shadow 和历史 adapter 复现。五类型、GPPO-History、公平增益和真实实时控制周期仍是下一研究入口。”

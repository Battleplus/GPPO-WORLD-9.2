# M-10 服务器复现手册

## 环境前提

使用 Python 3.10.12、Torch 2.2.2+cu121 和 Gymnasium 0.29.1。训练只在 `172.17.27.173` 的专用新目录执行。不要停止现有 TensorBoard，不把服务器绝对路径写成通用安装步骤。

## 从 Release 恢复

Release：[m10-meeting-research-v1-20260907](https://github.com/Battleplus/GPPO-WORLD-9.2/releases/tag/m10-meeting-research-v1-20260907)。下载训练包、PPT 和 PDF 后，先按 Release API digest 复核，再解包训练包。

1. 下载 `m10-training-artifacts-20260907-v2.tar.gz`，核对 SHA-256：`8c883d7cc7213ed724dd86e2a99645f30e5a2fca084fc75df42ace5ea22d6312`。
2. 解包到新的空目录，先核对归档内 `m10-source-20260907-v3.tar` 的 SHA-256：`77321bb99bc400f238b7ad505c603f87267f9632ea810a319eee684eaa828ba6`。
3. 解包源码归档，运行完整环境因果验收：

```text
python tools/run_m10_causal_acceptance.py --output <new-run>/causal-acceptance.json
```

4. 运行最小 pilot 或指定矩阵。矩阵入口不会下载文件、安装全局依赖或启动训练以外的进程：

```text
python tools/run_m10_training.py --mode pilot --output <new-run>/pilot --device cuda --steps 256 --world-episodes 16 --world-epochs 10 --seeds 1101
python tools/run_m10_training.py --mode matrix --output <new-run>/matrix --device cuda --steps 1024 --world-episodes 64 --world-epochs 30 --seeds 1101,2203,3307 --trigger-threshold 0.2
```

5. 结果入口是 `matrix-results.json`。完整 checkpoint、world-model、optimizer 状态和逐 seed 记录在训练归档的 `output/` 下。测试集只用于最终报告，不参与选择。

## 结果与限制

本轮服务器 causal acceptance 为 7/7，正式矩阵为 5 变体×3 seeds×1024 steps。训练依赖既有环境；runbook 不宣称任意新机器离线安装成功。返航/换电/充电仍待确认。

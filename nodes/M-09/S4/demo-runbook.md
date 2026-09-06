# 演示运行手册

1. 固定 source/target/baseline commit、policy/WM/calibration/config hash，确认服务器 Python/Torch/CUDA、磁盘和 GPU 空闲，并选择新目录。
2. 用 `tools/run_s4_read_only_demo.py` 在 S1-R2 的 60 条固定 tape 上运行 A-off/A-on；保存每条 trace、pair signature、Shadow/context counters 和 fault fixtures。
3. 用 target commit `69e3be5931deea7371df77d75fb14f2f5bdeab72` 的 `tools/evaluate_t05_server_checkpoint.py` 运行 B：EAWM-GPPO seed1101、step50000、100 条 held-out tapes。
4. 汇总 trace 与安全计数；任一真实环境/信念/mask/version/动作提交写入非零，或 A pair 不等价，均不得宣称通过。
5. 服务器输出先打包，再 SCP 到本地；独立计算 archive/member SHA-256 后才建立 Release。API digest 与 CDN 独立下载结果分开记录。

本次实际独立目录：`/home/user1/s4-runs/20260906-read-only`；既有 TensorBoard 与其他进程未触碰。

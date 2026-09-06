# S5 独立复现手册

本手册使用“交付包 + 已安装环境”的模型：服务器环境是可复用前置条件，不在本轮宣称任意新机器自动安装成功。所有绝对服务器目录只属于本次证据记录，不作为用户通用路径。

## 恢复顺序

1. 取得 `m09-s5-source-delivery-20260906.tar.gz`、`m09-s5-server-artifacts-20260906.tar.gz`，先核对 SHA-256；源归档为 `b4db4bca...5db0b4f84`，服务器归档为 `886c8ff4...cf88bb9f`。
2. 在新目录解包源归档，不使用开发目录；准备 Python 3.10.12、Torch 2.2.2+cu121、Gymnasium 0.29.1 环境。
3. 准备 A：纯 GPPO checkpoint `8c11eabb...fa253b1`、S1-R2 tape 生成器、Shadow 代码。运行最小代表性 OFF/ON：normal、energy_insufficient、uav_damage、communication_interrupt、composite_three_factor 各 1 条。
4. 在同一新目录运行 `tools/run_s4_read_only_demo.py` 的故障合同等价夹具，或使用归档内的 S5 runner，记录 no-context、reset、exception、stale-before、stale-after、timeout、synthetic OOD、disabled。
5. 准备 B：target commit `69e3be5...ab72` 的 evaluator、frozen baseline `2a9bb9f...51f9`、EAWM policy、world、calibration 和 held-out Test bank。只运行 EAWM-GPPO seed1101 的历史复现入口，不重复四组×三 seed 矩阵。
6. 记录命令、退出码、stdout/stderr、输入和输出哈希；输出必须存放在新的复现目录。任一模型/配置/target/baseline hash 不匹配就停止，不做性能声明。
7. 服务器输出按“输出 → 本地 SCP → 本地 SHA-256 → GitHub Release → 独立 CDN 下载”顺序封存。

## 本次实际复现

服务器新目录中的 A 最小复现退出码 0：5 个场景 OFF/ON 全部签名相等；policy state unchanged、world frozen and unchanged 为 true。B evaluator 退出码 0：100 tapes、635 decisions；逐 trace diagnostics 重新计数 `latent_adapter_used=true` 为 487，Shadow `valid_count=577`、`fallback_count=58`，其中 high uncertainty 11、OOD 47；timeout/stale-before/stale-after 为 0；所有安全写入/提交计数为 0。

## 不做的事情

- 不运行新训练，不覆盖旧结果，不修改 main，不强推分支。
- 不把 A 的 Shadow published context 写成 served latent。
- 不把 B 的历史消费结果写成 A 的公平提升。
- 不把 synthetic OOD、同步 post-call timeout 或单机资源状态扩展为生产/实时保证。

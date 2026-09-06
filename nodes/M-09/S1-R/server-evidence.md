# S1-R 服务器证据

- 主机：`user1@172.17.27.173`，用户私有隔离环境 `/home/user1/s1-gppo-venv`。
- checkpoint：`runs/GPPO/seed1101-attempt-2/models/gppo_seed1101_step50000.pt`，沿用 S0/S1 锁定版本。
- 固定 tape：原 S1 `make_tape`，六类各 10 条，共 60 条；未替换失败 tape。
- 运行输出：`s1r-evidence-20260906/s1r-acceptance.json` 与 `s1r-summary.json`。
- 归档 SHA-256：`d160fcb03d8e5a54cf0a2e963211e59d529be90482ba665f965e846d3f902f97`。
- 二次下载：同一 SHA-256；未进行训练、未终止其他进程、未修改共享环境。
- 服务器脚本和契约随归档保存，便于独立复算。

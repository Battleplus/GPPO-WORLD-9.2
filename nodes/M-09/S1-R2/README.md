# S1-R2 因果时序与低置信度确认专项修复

本目录只覆盖 S1-R2，不启动 S2、不训练、不改写 S1/S1-R 历史证据。

本地隔离复核已通过原六类固定场景 60 条 tape：60/60 结束并完成，场景断言 0，因果审计违规 0，采集器安全违规 0，约束违规 0，非法有效动作 0。新增专项 fixture 单独记录了未来事件配对、payload confidence 传递、证据不足 SUSPECTED、两源低置信度 CONFIRMED、过期和矛盾证据。

服务器复跑已在独立目录 `/home/user1/s1-r2-runs/20260906-v2` 完成并通过；服务器归档 SHA-256 为 `016b9608a1090c95cb41375e35f548cfa5e38fda9716b41a107ee2c7ebcbcc59`，下载回本地后二次校验一致。现有进程未停止，旧运行未覆盖。

历史 S1-R 归档保持原样：[m09-s1r-server-artifacts-20260906.tar.gz](../S1-R/m09-s1r-server-artifacts-20260906.tar.gz)。本次本地修复结果见 [local-acceptance.json](local-acceptance.json)，规则见 [protocol.md](protocol.md)。

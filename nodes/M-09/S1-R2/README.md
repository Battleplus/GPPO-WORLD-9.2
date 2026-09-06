# S1-R2 因果时序与低置信度确认专项修复

本目录只覆盖 S1-R2，不启动 S2、不训练、不改写 S1/S1-R 历史证据。

本地隔离复核已通过原六类固定场景 60 条 tape：60/60 结束并完成，场景断言 0，因果审计违规 0，采集器安全违规 0，约束违规 0，非法有效动作 0。新增专项 fixture 单独记录了未来事件配对、payload confidence 传递、证据不足 SUSPECTED、两源低置信度 CONFIRMED、过期和矛盾证据。

服务器复跑尚未完成：`user1@172.17.27.173` 可达，但当前可用 SSH 身份均被拒绝，未猜测密码、未修改共享环境、未伪称服务器通过。因此本阶段最终状态保持 `blocked`，直到服务器认证条件补齐后再执行独立目录复跑。

历史 S1-R 归档保持原样：[m09-s1r-server-artifacts-20260906.tar.gz](../S1-R/m09-s1r-server-artifacts-20260906.tar.gz)。本次本地修复结果见 [local-acceptance.json](local-acceptance.json)，规则见 [protocol.md](protocol.md)。

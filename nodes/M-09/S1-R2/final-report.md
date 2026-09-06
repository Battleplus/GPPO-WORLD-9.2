# S1-R2 最终报告

本地隔离修复后的原 60 条验收通过：60/60 episode 结束并完成，6 类场景断言全部通过，future-input 0，约束/非法有效动作/采集器安全违规均为 0。新增专项 fixture 也通过：弱 payload 被实际消费、单源低置信度为 SUSPECTED、两源 Region vacancy 为 CONFIRMED、过期为 EXPIRED、矛盾为 FALSE_ALARM。

修复前的本地复现为复合场景 10 条 `low_confidence_injection_not_consumed`，弱观测被硬编码成 0.95；修复后观测为 0.55 且不被单源确认。旧未来事件计数属于动作后观测与旧决策时刻比较造成的审计误报；任务说明所称 30、旧文字报告所称 20、旧 JSON 所称 0 存在证据版本差异，已在根因报告中保留并说明，不能逐项伪复算。

服务器复跑已通过：固定 60 条全部完成，服务器端 future-input 0、场景断言失败 0、约束违规 0、采集器安全违规 0。服务器归档已下载并独立解包验证，SHA-256 为 `016b9608a1090c95cb41375e35f548cfa5e38fda9716b41a107ee2c7ebcbcc59`。因此 S1-R2 可判定为 `passed`；S2 仅满足前置验收条件，仍未启动，本次没有训练、没有覆盖历史 Release。

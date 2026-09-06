# S4 接口合同

## 只读边界

`ShadowRuntime` 只接收 `ShadowRequest`，其 graph/evidence 在构造时脱离环境并冻结；它没有环境、belief、action-mask、版本、ACK、lease 或 command writer 引用。`PostActionShadowEnv` 是唯一执行入口：先让原环境处理 proposal，再对 accepted executed action 构造 request。

## 版本与消费

- request 的 graph/action version 是决策时刻版本；expected post versions 是执行成功返回后的版本。
- `ShadowRuntime.observe` 在推理前后读取版本；任一不一致返回 `stale_before`/`stale_after`，不提交隐藏状态。
- 有效结果转换为 `LatentContext`，只能被相同 variant/version 且同时匹配 post graph/action version 的下一次决策读取。
- `LatentContextStore` 对无上下文、失配、stale、reset 一律 fail-closed 返回零上下文。
- adapter 为无偏置 residual；disabled 或 zero/invalid context 直接返回原始 GPPO logits/value，旧 checkpoint 走 lossless fallback。

## 回退与限制

支持的理由包括 rejected execution、exception、stale before/after、timeout、OOD 和 high uncertainty；所有理由都产生 zero latent。timeout 是同步推理结束后的预算判断，不能等价为硬取消。OOD 证据只覆盖冻结 T-04 的 synthetic shift。

## 不变式

Shadow 不得调用环境 submit/step、runtime bridge command、belief 写入、action mask 写入或版本写入；策略不允许读取未来 truth-only 字段。S4 不训练、不改 checkpoint、不把历史 adapter 消费接入写成 S3 纯 GPPO 等价结果。

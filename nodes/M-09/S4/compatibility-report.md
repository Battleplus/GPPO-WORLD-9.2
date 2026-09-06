# 兼容性报告

## A：兼容

S3 的三类型 GPPO seed1101 checkpoint（4 UAV/4 Region/3 Target，17 action contract）可由冻结 GPPO-8.29 环境加载。T-04 EAWM world model 与 `snapshot_from_gppo` 输入合同匹配，Shadow 通过 `PostActionShadowEnv` 只在 accepted executed action 之后接收 detached pre-action graph/evidence。A-on 的上下文被发布到私有 store，但 pure GPPO policy 不读取它，因此只验证 side-car 安全与行为等价。

## B：兼容并完成

历史 `EAWM-GPPO/seed1101/step50000` checkpoint 的 metadata、adapter format、训练配置、target commit、baseline commit、world checkpoint 和 calibration 均与 T-05 冻结清单匹配。正式 evaluator 在 CUDA 上运行 100 条 held-out tapes、635 个决策；第一个决策可无上下文，后续 valid context 被真实 adapter 消费 487 次（`latent_adapter_used=true`）。这是历史 adapter-policy 接入证据，不是 S3 纯 GPPO 的等价性能结论。

## 边界

S1-R2 的执行/确认链仍由原环境负责；S4 没有把五类型图、返航/换电/充电或不存在的 GPO 来源接入。超时是同步推理完成后的 fail-closed gate，不是硬线程取消；OOD 是 T-04 synthetic feature-range shift，不是真实未见任务泛化。

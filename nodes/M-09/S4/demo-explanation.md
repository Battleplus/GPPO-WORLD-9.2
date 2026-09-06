# 演示说明

## A

off 直接由冻结 S3 GPPO 在固定 tape 上产生 proposal 并走原始 submit/ACK/stale/环境链；on 在同一位置加上 `PostActionShadowEnv`。on 的 WM 调用发生在执行成功之后，结果只能进入私有 latent store，不能提交动作、改 action mask、改 belief 或改版本。60/60 tape 的轨迹签名和回报完全一致，说明接入是 side-car。

## B

B 载入历史 T-05 EAWM-GPPO adapter checkpoint，并绑定同 seed 对应的 `eawm_hard_seed20260903.pt`。adapter 在下一次决策读取匹配的 post graph/action version context；首决策无 context 属于 reset 后预期行为，随后 487/635 个决策真实使用 latent adapter。B 的结果只证明接口和消费链可复现，不证明相对 GPPO 的性能增益。

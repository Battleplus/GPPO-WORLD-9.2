# 5-8 分钟汇报讲稿

## 1. 交付判断（约 40 秒）

今天不是宣布研究目标全部完成，而是交付冻结与复现验收。默认入口 A 保持纯 GPPO，世界模型可关闭或只读观察；历史入口 B 单独呈现，避免把两种系统混成一条性能结论。S3 明确跳过且未训练，因为当前交付问题是合同、证据和边界，不是已经证明需要新权重。

## 2. 当前真实系统（约 40 秒）

代码实际是 UAV、Region、Target 三种图节点，每类 4/4/3；动作是 16 条 UAV-Region 边加 NOOP，共 17。Task 是 UAV 状态枚举，Event 是可重放记录，不是额外节点。因此会议提到的五类型版本没有在当前资产中找到，本次不画成五类型。

## 3. 扰动与真值边界（约 40 秒）

策略只能使用决策时刻前已经到达并确认的 belief/evidence。能量不足、节点损毁、通信中断和低置信度在本轮分别属于执行门禁、事件/回退、底层通信机制或确认合同的证据。策略可见输入、环境执行真值、离线评估指标三者分开记录；世界模型不能直接发 actuator action。

## 4. 功能与安全证据（约 45 秒）

S1-R2 在固定 60 条 tape 上通过：future-input 0、非法有效提交和采集污染为 0。关键修复是保留 payload 的 0.55 confidence，并将低置信度单源 Region vacancy 保持为 SUSPECTED；两源才 CONFIRMED。S4 A 的 OFF/ON 全量 60/60 等价，Shadow 的环境、belief、mask、version 写入和动作提交全为 0。

## 5. 延迟与优化（约 45 秒）

S2 用同一 checkpoint、6 类×10 tape、CPU/cuda:0、5 次交错重复测量。`inference_mode` 使端到端均值 CPU 4.277103→4.150364ms，GPU 5.673699→5.489172ms；配对 tape-group CI 均不跨 0。纯策略前向是主要段，但不能由这组数据推断算法层 CPU/GPU 优劣，也不能声称实时达标或复现“慢 3-4 倍”。

## 6. 两条世界模型路径（约 50 秒）

A 是纯 GPPO + Shadow side-car：context 被发布到私有存储，但 pure policy 不消费，所以 zero-context parity 预期成立。B 是历史 EAWM-GPPO：在独立复现的 635 decisions 中 487 次真实 `latent_adapter_used=true`。B 的世界模型、adapter 和 calibration 都有精确哈希，但 B 不替代 A，也没有新增训练。

## 7. 回退边界（约 40 秒）

异常、过期前后、timeout 和 OOD 都 fail closed 到 zero context。timeout 的准确含义是 post-inference gate，不是中断一个已经进行的同步调用；OOD 269.0106024867358 来自特征整体平移 +3 的 synthetic fixture。它说明门禁路径能工作，不说明生产 OOD 泛化。

## 8. 负结果与未完成项（约 40 秒）

没有五类型源码、模型和数据合同；没有 GPPO-History 的公平对照，也没有稳定策略增益。当前 energy/damage 的通过主要证明执行链安全和回退，不应说成策略自主学会了能量/损毁语义。episode end、task completed、infeasible、deadline、执行拒绝和策略自主性也不能互相替换。

## 9. 下一优先级（约 35 秒）

下一步先补会议版本的可验证源码和五类型合同，再固定控制周期、规模、普通 PPO 与 GPPO-History 的 paired 数据和多 seed 训练预算。只有真实 held-out 回报与安全指标同时改善，才谈世界模型增益；T-06 想象规划仍是可选研究，不属于本次交付。

## 10. 复现与结束（约 35 秒）

交付包包括源归档、服务器归档、A/B 入口、PPTX/PDF、脚本和问答；新目录复现退出码均为 0，服务器归档与本地下载 SHA-256 一致并独立解包。实际评审尚未举行，9/13 冻结和 9/15 汇报仍待确认。

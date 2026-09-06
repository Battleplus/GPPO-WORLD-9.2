# S4 世界模型只读接入与安全回退协议

## 范围

本阶段只验证只读世界模型 side-car、版本绑定上下文、故障回退和安全边界；不训练、不更新策略权重、不改变 GPPO 动作空间与原有执行链，也不进入 S5。

## 冻结输入

- A 使用 S3 冻结的 GPPO checkpoint（seed 1101，50000 accepted decisions）和 S1-R2 的 6 个场景 × 10 条固定 tape，共 60 条；策略不读取世界模型上下文。
- A-off 是同一 checkpoint、同一 tape、同一确定性动作与原始环境；A-on 在同一环境外包裹 `PostActionShadowEnv`，执行成功后才调用 Shadow，并把结果写入私有上下文存储。
- B 仅使用 T-05 已存在、逐项匹配的历史 adapter-policy、世界模型和校准；若任一 hash、版本、结构或运行时前置条件不匹配，则 B 不运行且不得作策略消费声明。
- 世界模型和 adapter 均为 eval/frozen；Shadow 输入只允许决策时刻的图快照、已确认且不晚于决策时刻的证据、已执行动作和版本字段。

## 数据流与门禁

`visible decision graph/evidence -> ShadowRequest -> WM prediction -> calibration/version gates -> zero-or-latent context -> next GPPO decision -> original submit/ACK/stale/energy/safety chain`。

Shadow 只接收已接受的执行结果；stale 或 execution rejection 不进入 Shadow。上下文必须同时匹配 `model_variant`、`model_version`、`post_graph_version` 和 `post_action_version`，否则返回 zero-context。reset 清空隐藏状态和上下文。

## 正式运行与故障夹具

正式运行记录 A 60-tape ON/OFF paired trace、Shadow 版本/输入 hash、环境/信念/action-mask/version 写入计数和 policy state hash。故障夹具覆盖 disabled/no-context、reset、invalid/exception、stale-before、stale-after、timeout 和 synthetic OOD；timeout 明确是推理完成后的 fail-closed budget gate，不宣称硬线程取消。OOD 使用 T-04 已冻结的 synthetic feature-range shift，不宣称真实未见任务泛化。

通过条件：A 两臂逐 tape 轨迹签名、回报、终止状态和原始安全字段完全相等；Shadow 真实环境/信念/mask/version/动作提交写入全为 0；每种故障均返回 zero-context 且理由准确；B 仅在真实 `latent_adapter_used`/context served 证据存在时声明完成。

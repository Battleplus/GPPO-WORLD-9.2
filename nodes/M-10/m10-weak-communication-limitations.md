# M-10 弱通信阶段限制与失败记录

- 通信参数（延迟、丢包、重排窗口、outage 区间、命令/ACK 丢失概率）是归一化仿真设定，不是真实网络测量。
- simulator 只实现断联中断执行；长期失联自主执行、返航、换电、充电没有作为 NOOP 或续租隐藏实现。
- 审计字节量是 canonical JSON UTF-8 代理；没有物理编解码器、链路带宽或重传协议，因此 retransmission=0 不能解释为真实网络性能。
- 最终详细评估覆盖 16 个 final-test episode、280 个延迟样本，P99 是描述性尾分位，不是长期稳定性或生产 SLA 证明。
- recovery audit 保留了事件、合法遥测和重规划时间；本复合 tape 中没有恢复后的有效 service，因此 service recovery delay 全为 null，未从平均值中删除或改成成功。
- pilot world model 的 event/done BCE 劣于训练阳性率基线；C 阈值 0.1 每步触发，未节省 actor。B rules 虽降低 actor/world 调用，任务完成仍为 0，不能包装成收益。
- formal matrix 为每组 3 seed、12,288 环境步、有限 tape；支持受限描述性结论，不支持收敛、普遍化或统计显著性结论。
- 服务器 `m10-test-venv` 仍未安装 Torch/NumPy；训练和详细评估只读使用既有 `/home/user1/s1-gppo-venv`（Python 3.10.12、Torch 2.2.2+cu121、NumPy 1.24.4），没有修改共享环境。
- 历史旧 pinned GPPO baseline 缺失的 skip 仍按历史报告保留，不能冒充本阶段覆盖。
- 返航/换电/充电是否属于本次最低验收、真实控制周期、竞赛任务规模和汇报日期待用户确认；真实部署和人工评审未发生。

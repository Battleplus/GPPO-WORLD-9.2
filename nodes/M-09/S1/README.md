# M-09 S1 基础功能阶段

状态：`passed`

本阶段以 S0 提交 `0bcbcdb7475cabe9cfc69f6fcd9e51aaa0519cde` 和锁定的
`GPPO-Adaptive / seed=1101 / step=50000` 为起点。S1 的验收协议已冻结，
随后在指定服务器的用户私有隔离环境中完成了 S1-A、S1-B 和 S1-C。旧 checkpoint
没有被重新训练，新增约束保持在执行/评估层。

## 当前结论

- checkpoint、T-05 配置、100-tape 资产和两个冻结 checkout 均在指定服务器上找到，哈希与 S0 记录一致。
- `dporl` 的首次尝试确实因 Python 3.9.20 不支持 `dataclass(slots=True)` 失败；随后使用 `/home/user1/s1-gppo-venv` 的 Python 3.10.12/Torch 2.2.2+cu121/Gymnasium 0.29.1 完成复现。
- S1-A 完成 100 条原始 GPPO held-out tape 基础执行，S1-C 完成六类各 10 条固定 tape，共 60 条逐决策轨迹。
- 未训练、未终止其他任务、未修改共享环境，也未修改旧 Test 或历史阈值。

证据和协议见：

- [协议](protocol.md)
- [实现与边界](implementation.md)
- [兼容性结论](compatibility.md)
- [场景清单](scenario-manifest.json)
- [运行阻碍记录](failed-records.md)
- [最终报告](final-report.md)
- [轨迹清单](trace-manifest.json)
- [服务器证据与汇总](server-evidence.json)
- [服务器产物归档](m09-s1-server-artifacts-20260906.tar.gz)

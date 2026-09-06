# M-09 S1 基础功能阶段

状态：`blocked`

本阶段以 S0 提交 `0bcbcdb7475cabe9cfc69f6fcd9e51aaa0519cde` 和锁定的
`GPPO-Adaptive / seed=1101 / step=50000` 为起点。S1 的验收协议已冻结，
但在 S1-A 的服务器复现入口处被实际运行时阻塞，因而没有把未执行的功能或
60 条场景结果标记为通过。

## 当前结论

- checkpoint、T-05 配置、100-tape 资产和两个冻结 checkout 均在指定服务器上找到，哈希与 S0 记录一致。
- `dporl` 是 Python 3.9.20，而冻结 GPPO 代码使用 `dataclass(slots=True)`；直接执行在导入阶段失败。
- 可见 Python 3.10 环境缺少 `gymnasium`，且共享用户 Torch 的 CUDA 动态库不匹配；正在使用用户私有隔离环境尝试复现，不改共享环境。
- 因 S1-A 未完成，尚未进入 S1-B 实现、S1-C 六类 60 条固定 tape 验收，也没有训练或修改旧 Test/Release。

证据和协议见：

- [协议](protocol.md)
- [实现与边界](implementation.md)
- [兼容性结论](compatibility.md)
- [场景清单](scenario-manifest.json)
- [运行阻碍记录](failed-records.md)
- [最终报告](final-report.md)
- [轨迹清单](trace-manifest.json)

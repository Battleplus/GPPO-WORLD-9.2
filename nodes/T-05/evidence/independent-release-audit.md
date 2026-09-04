# T-05 独立证据与 Release 资产复核

复核日期：2026-09-04（Asia/Shanghai）

## Campaign 内容复核

在不修改训练目录的只读审计中，逐项重算并核对：

- 正式运行：12/12；
- checkpoint 文件与 SHA-256：24/24；
- run inventory 与实际文件：12/12；
- 固定 50k 评估：12/12；
- trace 文件与 SHA-256：1,200/1,200；
- 所有评估使用同一有序 Test tapes：100 条；
- PPO 配置除冻结的 group/seed 差异外一致；
- evaluation 与对应 50k checkpoint 的哈希链接：12/12；
- 环境、belief、action mask、version 和 Shadow action submission 写入/突变：全部为 0；
- 世界模型组 Shadow 延迟 Gate：9/9；
- 聚合 provenance、配置哈希、Test manifest 哈希和 `evaluated_no_checkpoint_selection` 状态：通过；
- 审计错误数：0。

GPPO 对照组按协议不实例化 world-model runtime，因此其 `shadow=null` 是正确的无 WM schema，不应被误判为缺失 Shadow 安全字段。

## 本地发布包复核

从服务器导出包下载到全新本地 staging 后复核：

- `release-assets-sha256.txt` 中 12 个被签名资产：12/12 SHA-256 匹配；
- 运行归档：108 个文件；
- 评估归档：1,224 个文件；
- campaign metadata 归档：119 个文件；
- 顶层 JSON 文件：全部可解析；
- 顶层 source inventory：1,451 个源文件；
- 总导出大小约 62.3 MB。

`release-assets-sha256.txt` 不自签名，因此 Release 共上传 13 个资产：12 个被清单签名的资产，加 SHA-256 清单本身。

## 结论

GitHub 草稿 Release 的 13 个附件已全量下载到全新目录，12 个内容哈希及校验清单自身与上传前副本全部一致（13/13）。本地测试 45/45 通过；Markdown 本地链接无断链，JSON 全部可解析。归档 1,427 个非 checkpoint 文本成员的凭据模式扫描未发现匹配，归档路径无绝对路径、父目录跳转或链接项。

复核结果为 `PASS`。该复核证明证据的完整性与协议执行，不改变消融的负性能结论。

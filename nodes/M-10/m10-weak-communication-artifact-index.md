# M-10 弱通信制品索引

服务器根目录：`/home/user1/m10-runs/20260907-weak-comm-v1`。本地下载目录：`E:\Z博士\m10-weak-comm-server-download`。

## 关键文件

- `pilot/tapes.json`：pilot 冻结 tape；SHA-256 `F746C487429ED00641421D0BD56E7AF9448FB9E5AFB0A135F2D8CC21EC9165D8`。
- `pilot/world-model.pt`：world model checkpoint、optimizer/recovery state；SHA-256 `AD356F648F85FC7D979AFF27FDAE8504EADB30F3CB666208108AE260697A734E`。
- `pilot/pilot-results.json`：pilot 三组结果；SHA-256 `D4EEBCF10AF620F808FF121AFDCFE81FE685543EA0D7B228DBF112F4BACF6983`。
- `formal/formal-results.json`：9 个正式 seed 结果和逐步训练记录；SHA-256 `6394344659A5D3C5EE59FDC8D662F18A1FF5D37FD093A2C401C55AF16B0F8FF3`。
- `formal/tapes.json`：formal 冻结 train/validation/historical/final/OOD tape；SHA-256 `F746C487429ED00641421D0BD56E7AF9448FB9E5AFB0A135F2D8CC21EC9165D8`。
- `formal/trigger-threshold-selection.json`：validation-only 阈值审计；SHA-256 `684346CA94123F1F71A8D851E31CE4DEF0F8F9A20A2B8109C1F7CFF7CDEAE2F1`。
- `formal/detailed-eval.json`：seed-1101 final-test 详细通信/恢复/执行/端到端时延审计；SHA-256 `EA169C3B6EE1588DA01151552F3C6B27580D9D9AB758EBD399E147C1C087E539`。
- `formal/weak-comm-contract-audit-r2.txt`：服务器 10/10 直接合同审计；SHA-256 `D047B2AFD6361FF68EA6D930A1B40B872E145C80E918D3944B255444838E5D45`。

`formal/formal/checkpoints/{A-graph5-base,B-graph5-world,C-graph5-triggered}/seed-{1101,2203,3307}.pt` 和对应 `formal/formal/records/` 保存全部 9 个 checkpoint、optimizer/recovery state、配置、逐 seed 评估与负结果。完整逐文件 SHA-256 清单随独立归档提供；历史 M-09/M-10/M-10-R/R2/R3 Release 通过状态文件索引，不重复覆盖或删除。

独立 Release：[m10-weak-comm-gppo-world-v1-20260907](https://github.com/Battleplus/GPPO-WORLD-9.2/releases/tag/m10-weak-comm-gppo-world-v1-20260907)，发布目标提交为 `106d2267ab397829ed8a437219f9b696b609f0cb`。下载复核：bundle `D4416A1D9CF892B247AB50507A623DCD70A9022E8CB9993F79227537BB4A183C`，source `D705E30CD9D6EA84A655720FF2ADAF2B91CEE37BCE7EDA895EF217FBF7EC82F5`；GitHub API asset digest 与本地下载一致。

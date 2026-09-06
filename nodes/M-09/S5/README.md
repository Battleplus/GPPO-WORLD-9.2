# S5：交付冻结、复现验收与汇报材料

日期：2026-09-06。S5 将 S0、S1-R2、S2、S3、S4 的可复用证据整理为一个候选交付包，并在服务器新目录完成独立复现。S3 的状态仍是 `skipped`：本阶段没有新增训练，也没有把历史结果改写成新实验。

## 交付结论

- A 是默认交付入口：冻结的纯 GPPO seed 1101 / step 50000，包含 S1-R2 因果时序与低置信度修复、S2 `inference_mode` 入口；世界模型关闭，或以只读 Shadow side-car 观察。S4 全量 60 条 paired tape 为 60/60 等价、回报差全为 0。
- B 是历史复现入口：EAWM-GPPO seed 1101 / step 50000 + 匹配的 EAWM-hard world model + T-04 calibration。它在新目录重跑 100 条 held-out tapes，635 decisions 中 487 次真实消费 adapter context，577 valid、58 fallback；B 不替代 A，也不是公平性能增益结论。
- 服务器最小代表性 A 复现为 5 个场景各一条 OFF/ON 配对，5/5 签名相等；异常、stale-before/after、timeout、synthetic OOD、reset/no-context 的 fail-closed 证据均已写入归档。
- 汇报材料明确列出五类型资产缺失、真实控制周期未确认、GPPO-History/五类型公平对照未完成、没有稳定策略增益结论等限制。

## 文件索引

- [claims-and-evidence.md](claims-and-evidence.md)：外部可见声明、证据位置、适用范围和限制。
- [release-candidate.json](release-candidate.json)：A/B 冻结入口、提交、模型和配置摘要。
- [reproduction-runbook.md](reproduction-runbook.md)：从归档恢复并执行最小复现的步骤。
- [reproduction-results.json](reproduction-results.json)：服务器独立复现结果及关键哈希。
- [server-evidence.json](server-evidence.json)：资源复核、服务器归档、本地下载和解包复核。
- [demo-script.md](demo-script.md)：3-5 分钟实际演示脚本。
- [speaker-notes.md](speaker-notes.md)：5-8 分钟逐页讲稿。
- [questions-and-answers.md](questions-and-answers.md)：汇报问答底稿。
- [limitations.md](limitations.md)：能力、证据和未完成研究边界。
- [final-report.md](final-report.md)：S5 最终报告。
- [slides/汇报.pptx](slides/汇报.pptx) / [slides/汇报.pdf](slides/汇报.pdf)：已渲染检查的可编辑汇报稿和 PDF。

## GitHub 归档

交付 Release：<https://github.com/Battleplus/GPPO-WORLD-9.2/releases/tag/m09-s5-delivery-freeze-v1-20260906>。Release 中的 `default.pptx`、`default.pdf`、源归档和服务器归档均已独立下载并按 SHA-256 校验；其中 `default.*` 是 GitHub 对中文文件名的归一化名称。

## S5 状态

| 状态项 | 结果 |
|---|---|
| `delivery_package_ready` | `true` |
| `reproduction_verified` | `true` |
| `slides_render_verified` | `true` |
| `archive_verified` | `true` |
| `rehearsal_status` | `materials_ready; user_rehearsal_pending` |
| `actual_review_status` | `not_held` |
| 目标冻结日 | 2026-09-13，待确认 |
| 目标汇报日 | 2026-09-15，待确认 |

实际导师/评审尚未举行，本目录不作“已验收”或“已同意”的表述。

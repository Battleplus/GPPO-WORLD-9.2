# 节点、checkpoint 与证据保存规范

## 1. 保存原则

每个 T 节点都是一个可审计的保存点。通过节点时必须同时保存：

1. 源代码 Git commit；
2. 完整配置及配置 SHA-256；
3. 数据集/切分 manifest 及 SHA-256；
4. seed、运行环境、依赖和硬件摘要；
5. 模型 checkpoint 及 SHA-256（该节点产生模型时）；
6. 原始日志、指标表、失败案例和报告链接；
7. 父 checkpoint、schema version、回退路径；
8. 节点验收人/时间与 `passed` 或 `failed` 结论。

仓库只保存小型文本证据和 manifest。大型 checkpoint 不直接提交普通 Git：使用 GitHub Release、Git LFS 或受控对象存储，并在 manifest 中登记不可变 URL 与 SHA-256。没有真实文件时，URI 和哈希必须保持空值，禁止伪造。

## 2. 命名

```text
gppo-world/<node>/<component>/<version>/<seed>

示例：
gppo-world/T-02/base-wm/v0.1.0/42
gppo-world/T-03/eawm-ges/v0.1.0/42
gppo-world/T-05/eawm-gppo/v0.1.0/42
```

建议通过节点后创建 annotated tag：

```text
node-t00-pass-v0.1.0
node-t02-pass-v0.1.0
node-t05-pass-v0.1.0
```

标签只能指向证据齐全的提交，不得预先建立“pass”标签。

## 3. 节点目录

每个 `nodes/T-xx/` 至少包含：

```text
README.md                 # 目标、状态、Gate、结果和真实证据链接
evidence/                 # 后续按需建立
  run-manifest.json
  checkpoint-manifest.json
  metrics.json
  sha256sums.txt
```

本仓库已提供：

- [节点记录模板](../nodes/templates/NODE_RECORD_TEMPLATE.md)
- [checkpoint manifest JSON Schema](../nodes/templates/checkpoint-manifest.schema.json)
- [机器可读节点状态](../nodes/status.json)

## 4. 最小 checkpoint manifest 字段

| 字段 | 用途 |
|---|---|
| `artifact_id` | 全局唯一产物名 |
| `node_id` | T-00～T-06 |
| `status` | absent/training/candidate/accepted/rejected |
| `source_commit` | 训练代码提交 |
| `parent_artifact_id` | 继承关系与回退 |
| `schema_version` | 输入输出兼容性 |
| `config_uri/config_sha256` | 配置证据 |
| `dataset_manifest_uri/dataset_manifest_sha256` | 数据与 split 证据 |
| `seeds` | 可复现种子 |
| `checkpoint_uri/checkpoint_sha256` | 模型位置与完整性 |
| `metrics_uri/metrics_sha256` | 结果证据 |
| `environment` | Python/PyTorch/CUDA/硬件 |
| `created_at` | UTC 时间 |

## 5. 状态变更规则

```text
planned → in_progress → passed
                    └→ failed → in_progress（新 run_id）
blocked_by_T-xx → planned（前置节点 passed 后）
```

- `passed`：所有硬 Gate 有真实证据链接。
- `failed`：保留负结果、失败原因和对应配置，不覆盖历史。
- 修改验收阈值：必须产生新 schema/plan 版本，不能事后改阈值让已有结果通过。
- checkpoint 被撤销：manifest 标为 `rejected`，保留哈希和原因，禁止删除审计链。

## 6. GitHub 链接约定

节点首页使用相对链接，以便 fork/branch 仍可浏览；证据结论使用固定 commit permalink，避免 `main` 更新后内容漂移。Release 资产使用带版本号的 release URL，并用 SHA-256 校验。

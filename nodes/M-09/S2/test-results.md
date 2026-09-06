# 测试结果

- 项目 pytest：`98 passed`，使用独立临时目录并关闭无关自动插件加载。
- S1-R2 原 60 条服务器验收（优化后）：`passed`，60/60；future-input 0、场景断言失败 0、约束违规 0、采集器安全违规 0。
- S2 正式性能臂：CPU/GPU × baseline/优化 × 5 重复，共 20 个比较运行，全部退出码 0；每运行含 1 遍预热和 60 条正式 tape。
- 冷启动：CPU 3 次、GPU 3 次，全部退出码 0。
- 同等性比较：60/60 tape 的 actions、logits、graph hash、reward、结束分类和确认流水线全部一致。
- 基线仓库全套 132 项中 130 项通过，2 项既有 legacy 兼容测试仍因缺少 `sb3_contrib` 未覆盖，不计为通过。

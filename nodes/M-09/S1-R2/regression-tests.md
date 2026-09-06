# 回归测试

本地项目既有 S1-R 的 7 项契约测试保留不动，项目测试使用独立临时目录运行：`98 passed`。

新增基线回归：

- `test_low_confidence_payload_reaches_detector_and_stays_suspected`：通过；证明 payload 0.55 到达 detector，severity 独立，单源不会更新环境确认状态。
- `test_low_confidence_region_requires_two_independent_sources`：通过；证明第二个不同来源到达后才 CONFIRMED。
- 受影响模块两项定向测试：`2 passed`。
- 基线 `tests_random_event` 全套：132 项中 130 项通过，2 项既有 legacy 兼容测试因运行环境缺少 `sb3_contrib` 失败；非本次改动引入，未将其伪装为全绿。

本地原 60 条固定 tape：6 类 × 10，`passed`。专项 diagnostics 与原 60 条分开保存于 [diagnostic-summary.json](diagnostic-summary.json) 和 [scenario-summary.json](scenario-summary.json)。

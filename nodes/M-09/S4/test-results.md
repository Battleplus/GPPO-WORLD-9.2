# 测试与结果

- A 服务器正式 paired replay：60/60 signatures equal，60/60 return difference 0.0，Shadow audit 与 context/policy/world-model safety gates 全部通过。
- A Shadow trace：79 valid、1 high-uncertainty fallback；published valid 79、published fallback 1；真实 environment/belief/action-mask/version mutation 与 Shadow action submission 全为 0。
- Fault fixtures：无 context/read 后为 invalid；reset 将 valid context 清空；exception、stale-before、stale-after、timeout、synthetic OOD 均为 invalid + zero latent，理由分别为 `exception`、`stale_before`、`stale_after`、`timeout`、`ood`；OOD score 为 269.0106024867358。
- B 服务器 evaluator：EAWM-GPPO seed1101、100 tapes、635 decisions；Shadow valid 577、fallback 58（high uncertainty 11、OOD 47、timeout 0、stale 0）；environment/belief/action-mask/version mutation 与 Shadow action submission 全为 0；adapter consumption 487 次。
- 本地回归：S3 已有测试在隔离临时目录为 98 passed；S4 runner 已通过 Python 编译检查。默认 Windows 临时目录的历史权限错误未计为代码失败。

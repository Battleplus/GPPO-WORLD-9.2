# T-05 local test report

- Target code commit: `a4432a9527c73021d605f6960dfcc5b8d3e3b3c6`
- Baseline: `GPPO-8.29@2a9bb9f87b9d543df144f4d108ba970c924151f9`
- Command: `python -m pytest -q --basetemp .pytest-t05`
- Result: `44 passed in 2.33s`
- Scope: unit/contract tests and local small smoke only.

The run also executed `tools/validate_t05_local.py` against the real baseline environment and `eawm_hard_seed20260903.pt` (`eb8c13dd822f27511ed892a091833b1fd5b8d69ed28b044ec47a7e34a68b19cf`). All 21 local interface gates passed, including the actual command-rejection assertion that the on-policy proposal transition is retained while rejected execution enters neither Shadow nor the next context. The JSON evidence is `local-interface-validation.json`, SHA-256 `37101d2420296ce016635707ed4d1393e05d3921632dc73f00fd6ad8fb6660c4`.

This report does not contain the required server/GPU four-group ablation and therefore is not a T-05 pass record.

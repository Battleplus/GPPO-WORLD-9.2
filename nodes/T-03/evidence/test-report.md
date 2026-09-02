# T-03 test report

- Result: **PASS**
- Code commit: `1d02beb8cce6e90d2cf2d84abf69c9666ce73db3`
- Automated tests: `31 passed`
- Seeds: `20260903, 20260904, 20260905`
- Event schema SHA-256: `e359079e8bc7cb89684f50e438d423b49ff994aa2dcfb3cece5b8b66ae8407a7`
- EAWM-hard macro-F1: `0.466769 ± 0.004970`
- EAWM-hard macro-AUPRC: `0.431982 ± 0.013572`
- EAWM-hard rare-event recall: `0.153531 ± 0.021994`
- Maximum per-seed state/reward/cost degradation versus WM: `0.338545%` / `0.469180%` / `1.214437%`

All final per-seed gates passed. The first failed configurations remain downloadable release assets. T-01 has no TTL/expiry contract, so the `expire` evidence label is explicitly ineligible rather than treated as an all-negative target.

Protocol disclosure: The initial test results were inspected before the backbone learning-rate multiplier was frozen. The revision was also motivated by matching validation degradation; both failed pre-freeze runs are retained. Final results are repeated over three seeds but are not represented as a pristine first-look test evaluation.

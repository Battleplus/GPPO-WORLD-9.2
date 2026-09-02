# T-04 test and safety report

- Result: **PASS**
- Code commit: `65d7a16240484797b7596c32811762f2cdfff7e9`
- Repository tests: `37 passed`
- Real baseline audit: `GPPO-8.29@2a9bb9f`, `12` post-action Shadow calls
- State-change ECE raw/calibrated: `0.072046` / `0.072046`
- Continuation ECE raw/calibrated: `0.101731` / `0.082843`
- Risk coverage state MAE at 50%/100%: `0.038106` / `0.055653`
- Complete observe P50/P95/P99: `5.6875` / `6.9861` / `8.0455` ms
- Synthetic OOD AUROC/recall: `1.000000` / `1.000000`
- ID OOD false-positive rate: `8.588957%`

All belief/action-mask/graph-version/action-version/action-submission counters are zero. The real baseline environment snapshot, runtime belief hash, action mask and versions were unchanged before/after every Shadow call; fail-fast spies on action/execution/belief mutation APIs were never invoked.

Limits: OOD uses a synthetic +3 normalized-feature range shift, while all T-01 splits share the same seven profile families. This proves fallback mechanics, not production unseen-mission generalization. Timeout is fail-closed after inference completes, not hard worker cancellation. Shadow does not influence GPPO actions; downstream value remains T-05.

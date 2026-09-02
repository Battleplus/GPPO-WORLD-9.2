# T-02 verification report

- Source implementation: `68d55db239a9992b40f0b485d4e7fec26aa2b136`
- Baseline: `Battleplus/GPPO-8.29@2a9bb9f87b9d543df144f4d108ba970c924151f9`
- Runtime: Python 3.11.5, PyTorch 2.5.0+cpu, NumPy 2.0.2, Windows CPU
- Seed: `20260902`

## Commands and results

```text
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 D:/anaconda/python.exe -m pytest -q
24 passed

cd GPPO-8.29-baseline/ppo_allocation
PYTHONPATH=. D:/anaconda/python.exe -m unittest \
  tests_random_event.test_random_event_core \
  tests_random_event.test_random_event_training \
  tests_random_event.test_concurrency_invariants \
  tests_random_event.test_event_runtime_integration
Ran 50 tests
OK

D:/anaconda/python.exe tools/train_t02_world_model.py \
  artifacts/T01/dataset artifacts/T02 \
  --epochs 80 --patience 15 --seed 20260902
exit code 0; result PASS; 11/11 gates true
```

## Reproducibility and safety checks

- Two consecutive final-code runs produced Graph-WM SHA-256
  `942c3cd5f99efe6e41fd889817598657e158a9db5d7c49e42cfacb7dd684c597`.
- Two consecutive final-code runs produced Flat-GRU SHA-256
  `ec778fe65e0a2bfd00e99d519976dc2463237586776f74d15b65b2dc609b3710`.
- The model signature has no post-action `delta_time` input.
- T-01 input audit: split overlap 0, truth-only online fields 0, illegal executions 0,
  graph-version mismatches 0, and behavior-checkpoint hash verified.
- Legal counterfactual selection observed 0 illegal alternatives and branches from the same hidden state.
- Graph and Flat-GRU checkpoint roundtrip maximum absolute output difference is 0.

## Transparent limitations

- Graph-WM state MAE improves only slightly over last-value (`0.0487038303` versus `0.0490300734`).
- The equal-budget Flat-GRU state MAE is lower (`0.0460505038`); this negative graph-vs-flat comparison is retained.
- No-action state degradation has a 95% CI crossing zero. The hard action-use Gate is the legal counterfactual
  test, whose state/reward/cost CI lower bounds are all positive.
- T-02 does not modify GPPO and does not claim downstream policy improvement.

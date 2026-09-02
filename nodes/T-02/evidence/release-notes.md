# T-02 causal Graph World Model v0.1.0

Source implementation: `68d55db239a9992b40f0b485d4e7fec26aa2b136`

This release contains the accepted seed-20260902 Graph World Model checkpoint, the parameter-budget-matched
Flat-GRU baseline checkpoint, machine-readable PASS metrics, strict T-01 input audit, complete training histories,
and the retained pre-calibration failed run.

Key accepted results:

- no post-action future interval is accepted by the model interface;
- all 8 registered relation types are included in the 384-dimensional state target;
- held-out Graph-WM state MAE is 0.0487038303 versus last-value 0.0490300734;
- legal counterfactual actions worsen state, reward, and cost error with positive episode-bootstrap 95% CIs;
- uncertainty/error Spearman correlation is 0.632530855;
- Graph and Flat-GRU checkpoint roundtrip maximum absolute difference is 0;
- Graph/Flat parameter budget gap is 0.3028%;
- 1/3/5-step state MAE is reported transparently.

The no-action state degradation CI crosses zero and remains recorded as a diagnostic negative result. It is not
used to replace the stricter legal-action counterfactual hard Gate.

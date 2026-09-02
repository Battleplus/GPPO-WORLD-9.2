# T-00 causal-input correction

The original T-00 contract exposed `next_decision_time - decision_time` through `WorldModelInput.delta_time`.
Because the next decision time is only known after action execution and event absorption, this field could leak
future timing information into training.

Implementation commit `68d55db239a9992b40f0b485d4e7fec26aa2b136` removes that field from the online model input and from the
Graph/Flat world-model signatures. `next_decision_time` remains only in the offline transition target record.

Verification:

- contract test asserts `WorldModelInput` has no `delta_time` attribute;
- training Gate inspects the model signature and requires the future interval input to be absent;
- all 24 repository tests pass after the correction;
- the strict T-01 re-audit still reports split overlap 0 and truth-only online field count 0.

This corrective evidence supersedes the original timing-field interpretation while preserving the serialized
T-01 target records and their hashes.

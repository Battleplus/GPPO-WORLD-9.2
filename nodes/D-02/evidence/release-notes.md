# D-02 frozen adapter development diagnostics v0.1.0

9 fixed 50k policies × 12 fresh development tapes × probe on/off = 216 episodes.

- 108/108 matched behavioral replays pass; 623 decision probes.
- Environment/belief/mask/version/Shadow submission mutations: zero.
- Original checkpoints unchanged; no retraining, no T-06.
- 60 unit/regression tests pass; independent audit checks 270 source files and 216 traces.
- 262 diagnostic files archived; existing T-03/T-05 input checkpoints are not duplicated.

The probe compares the co-trained embedded base and adapter of the SAME checkpoint, not an independent GPPO baseline. EAWM changes 17 preferred actions among 170 latent-enabled decisions on this small development set. This is not a causal benefit or formal performance claim. CPU runtime differs from the original Linux CUDA experiment.

报告：[D-02 结果及 D-03 假设判定](https://github.com/Battleplus/GPPO-WORLD-9.2/blob/main/nodes/D-02/evidence/final-report.md)

下一步：[D-04 验证设计，尚未执行新训练](https://github.com/Battleplus/GPPO-WORLD-9.2/blob/main/nodes/D-04/README.md)

# luna_worker T-05 audit resolution

The read-only audits found that rollout/update sidecar alignment was causally correct, then identified execution, recovery and server-provenance gaps. Commits `05e7e8602cdf2be925aa8afc59655f106cd7f734` and `a4432a9527c73021d605f6960dfcc5b8d3e3b3c6` resolve them as follows:

1. A legal proposal repaired to NOOP by the pinned execution layer is treated as execution rejection. It does not call Shadow, publish latent, or mark the Shadow transition accepted.
2. `LatentPPOTrainer.load` now dispatches adapter and legacy checkpoints, restores optimizer/history only when structurally compatible, and always resets/omits online context.
3. Shadow input now includes only events already present in confirmed belief by decision time; future confirmation and truth tracker fields are not read.
4. `PostActionShadowEnv` and `LatentPPOTrainer` reject training-mode or trainable world models and assert that WM parameters are absent from the PPO optimizer.
5. Explicit contexts are bound to model variant, model version, graph version and action version. The rollout buffer stores and revalidates both versions before PPO update.
6. Every real Shadow call compares environment snapshot hash, belief hash, action mask and both live versions immediately before/after inference.

The audit also exposed a pinned-baseline defect: its command-rejection branch references an undefined `self.noop_action`. T-05 installs only the already-frozen `action_space.n - 1` NOOP constant. The injection test now reaches fail-closed behavior and confirms zero Shadow inference.

A second audit challenged the rejected-transition semantics. The final contract makes the distinction explicit: GPPO's MDP action is the sampled command proposal, while command rejection/fail-closed NOOP is the environment transition caused by that proposal. PPO therefore retains the proposal, original log-prob, reward and next state to preserve an unbroken on-policy trajectory. Shadow does not update because no executed action was confirmed, and the next context fails closed to zero. The actual baseline injection proves one rejected proposal yields one proposal transition, zero Shadow calls and invalid next context.

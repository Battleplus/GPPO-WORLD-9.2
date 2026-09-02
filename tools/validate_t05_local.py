"""Local-only T-05 interface/safety smoke; never a performance claim."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys

import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_safe(value):
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline-root", required=True)
    parser.add_argument("--world-checkpoint", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    baseline_root = Path(args.baseline_root).resolve()
    world_checkpoint = Path(args.world_checkpoint).resolve()
    output = Path(args.output).resolve()
    sys.path.insert(0, str(baseline_root))

    from ppo_allocation.random_event.environment import (  # noqa: PLC0415
        ActionSubmission,
        RandomEventAllocationEnv,
    )
    from ppo_allocation.random_event.models import GraphActorCritic  # noqa: PLC0415
    from ppo_allocation.random_event.trainer import PPOConfig  # noqa: PLC0415
    from gppo_world.calibration import ShadowCalibration  # noqa: PLC0415
    from gppo_world.gppo_adapter import (  # noqa: PLC0415
        LatentAdapterConfig,
        LatentAugmentedActorCritic,
        LatentContextStore,
        freeze_world_model,
    )
    from gppo_world.gppo_shadow_env import PostActionShadowEnv  # noqa: PLC0415
    from gppo_world.gppo_trainer import LatentPPOTrainer  # noqa: PLC0415
    from gppo_world.model import EventAwareGraphWorldModel  # noqa: PLC0415
    from gppo_world.shadow import ShadowRuntime  # noqa: PLC0415

    calibration = ShadowCalibration.from_dict(
        json.loads((ROOT / "nodes/T-04/evidence/calibration.json").read_text(encoding="utf-8"))
    )
    world_model, _ = EventAwareGraphWorldModel.load(world_checkpoint, map_location="cpu")
    freeze_world_model(world_model)
    adapter_config = LatentAdapterConfig(
        latent_dim=world_model.config.hidden_dim + world_model.config.stochastic_dim
    )

    raw = RandomEventAllocationEnv(
        initial_seed=20260902,
        event_seed=2026090201,
        events_per_episode=3,
        max_decisions=14,
    )
    graph, _ = raw.reset(seed=20260902)
    torch.manual_seed(20260902)
    base = GraphActorCritic.from_graph(graph)
    base_logits, base_value, _ = base(graph)
    disabled = LatentAugmentedActorCritic(
        base,
        adapter_config,
        enabled=False,
        model_variant="GPPO",
        model_version="no-world-model",
    )
    disabled_logits, disabled_value, _ = disabled(graph)

    store = LatentContextStore(
        adapter_config,
        model_variant="EAWM-GPPO",
        model_version=f"{world_checkpoint.name}:{sha256(world_checkpoint)}",
    )
    runtime = ShadowRuntime(
        world_model,
        calibration,
        model_version=store.model_version,
    )
    env = PostActionShadowEnv(raw, runtime, store, model_variant="EAWM-GPPO")
    policy = LatentAugmentedActorCritic(
        GraphActorCritic.from_graph(graph),
        adapter_config,
        context_store=store,
        enabled=True,
        model_variant="EAWM-GPPO",
    )
    trainer = LatentPPOTrainer(
        env=env,
        variant="GPPO-Adaptive",
        config=PPOConfig(
            rollout_steps=12,
            update_epochs=1,
            minibatch_size=4,
            seed=20260902,
            device="cpu",
        ),
        model=policy,
    )
    buffer, rollout = trainer.collect_rollout()
    update = trainer.update(buffer)
    audit = env.audit()

    scratch = ROOT / "artifacts" / "T05-local"
    scratch.mkdir(parents=True, exist_ok=True)
    adapter_checkpoint = scratch / "adapter-roundtrip.pt"
    trainer.save(adapter_checkpoint)
    restored_env = RandomEventAllocationEnv(
        initial_seed=20260902, event_seed=2026090201, events_per_episode=3, max_decisions=14
    )
    restored, restored_metadata = LatentPPOTrainer.load(
        str(adapter_checkpoint), restored_env
    )
    legacy_checkpoint = scratch / "legacy-roundtrip.pt"
    base.save(
        legacy_checkpoint,
        extra={
            "variant": "GPPO-Adaptive",
            "ppo_config": asdict(trainer.config),
        },
    )
    legacy_env = RandomEventAllocationEnv(
        initial_seed=20260902, event_seed=2026090201, events_per_episode=3, max_decisions=14
    )
    legacy, legacy_metadata = LatentPPOTrainer.load(str(legacy_checkpoint), legacy_env)
    legacy_graph, _ = legacy_env.reset(seed=20260902)
    legacy_original, _ = GraphActorCritic.load(legacy_checkpoint)
    original_output = legacy_original(legacy_graph)
    fallback_output = legacy.model(legacy_graph)

    def rejection_case(stale: bool) -> dict:
        local_raw = RandomEventAllocationEnv(
            initial_seed=91, event_seed=9101, events_per_episode=2, max_decisions=8
        )
        local_store = LatentContextStore(
            adapter_config, model_variant="EAWM-GPPO", model_version="injection"
        )
        local_runtime = ShadowRuntime(world_model, calibration, model_version="injection")
        local_env = PostActionShadowEnv(
            local_raw, local_runtime, local_store, model_variant="EAWM-GPPO"
        )
        local_env.reset(seed=91)
        decision = local_env.begin_decision()
        if stale:
            local_raw.decision_version += 1
            action = decision.graph.noop_action
        else:
            action = int(torch.nonzero(decision.graph.action_mask[:-1], as_tuple=False)[0])
            local_raw.runtime_bridge.issue_assignment_command = lambda *a, **k: None
        _, _, _, _, info = local_env.submit_action(
            ActionSubmission.from_decision(action, decision)
        )
        return {
            "shadow_inference_count": local_runtime.counters["inference_count"],
            "stale_decision": bool(info.get("stale_decision", False)),
            "execution_rejection_count": local_env.audit().execution_rejection_count,
            "context_valid_after": local_store.read(
                local_raw.graph_version, local_raw.decision_version
            ).valid,
        }

    execution_rejection = rejection_case(False)
    stale_rejection = rejection_case(True)
    sidecars_aligned = all(
        int(graph_item.graph_version) == graph_version
        and (
            not context.valid
            or (
                context.post_graph_version == graph_version
                and context.post_action_version == action_version
            )
        )
        for graph_item, context, graph_version, action_version in zip(
            buffer.graphs,
            buffer.contexts,
            buffer.graph_versions,
            buffer.action_versions,
        )
    )
    gates = {
        "disabled_logits_bit_exact": torch.equal(base_logits, disabled_logits),
        "disabled_value_bit_exact": torch.equal(base_value, disabled_value),
        "legacy_checkpoint_loads_disabled": not legacy.model.enabled,
        "legacy_logits_bit_exact": torch.equal(original_output[0], fallback_output[0]),
        "legacy_value_bit_exact": torch.equal(original_output[1], fallback_output[1]),
        "adapter_checkpoint_restores": restored.total_steps == trainer.total_steps,
        "adapter_context_is_not_restored": restored_metadata["context_restored"] is False,
        "world_model_frozen": all(not parameter.requires_grad for parameter in world_model.parameters()),
        "world_model_eval": not world_model.training,
        "rollout_update_sidecars_aligned": sidecars_aligned,
        "valid_shadow_observed": audit.shadow_valid > 0,
        "decision_time_evidence_observed": audit.decision_evidence_items > 0,
        "real_environment_mutations_zero": audit.real_environment_mutation_count == 0,
        "real_belief_mutations_zero": audit.real_belief_mutation_count == 0,
        "real_action_mask_mutations_zero": audit.real_action_mask_mutation_count == 0,
        "real_version_mutations_zero": audit.real_version_mutation_count == 0,
        "shadow_write_and_submission_counters_zero": sum(
            getattr(audit, key)
            for key in (
                "belief_write_count",
                "action_mask_write_count",
                "graph_version_write_count",
                "action_version_write_count",
                "action_submission_count",
            )
        ) == 0,
        "execution_rejection_does_not_reach_shadow": (
            execution_rejection["shadow_inference_count"] == 0
            and execution_rejection["execution_rejection_count"] == 1
            and not execution_rejection["context_valid_after"]
        ),
        "stale_rejection_does_not_reach_shadow": (
            stale_rejection["shadow_inference_count"] == 0
            and stale_rejection["stale_decision"]
        ),
        "ppo_update_finite": bool(torch.isfinite(torch.tensor(update["policy_loss"]))),
    }
    result = {
        "format": "gppo-t05-local-interface-validation/0.1.0",
        "scope": "local interface/unit/small smoke only; not a performance or T-05 pass claim",
        "target_commit": subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True
        ).strip(),
        "baseline_commit": subprocess.check_output(
            ["git", "-C", str(baseline_root), "rev-parse", "HEAD"], text=True
        ).strip(),
        "world_checkpoint": world_checkpoint.name,
        "world_checkpoint_sha256": sha256(world_checkpoint),
        "rollout": rollout,
        "update": update,
        "buffer_transition_count": len(buffer),
        "audit": asdict(audit),
        "execution_rejection": execution_rejection,
        "stale_rejection": stale_rejection,
        "legacy_metadata": legacy_metadata,
        "gates": gates,
        "all_local_gates_pass": all(gates.values()),
        "formal_server_ablation_complete": False,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(json_safe(result), ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"all_local_gates_pass": result["all_local_gates_pass"], "gates": gates}))
    return 0 if result["all_local_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Evaluate one fixed T-05 50k checkpoint on the frozen held-out Test bank."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

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


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def git(path: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(path), *args], text=True).strip()


class DeviceModelProxy:
    def __init__(self, model: Any, device: torch.device):
        self.model = model
        self.device = device

    def act(self, graph: Any, deterministic: bool = True):
        return self.model.act(graph.to(self.device), deterministic=deterministic)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("group", choices=("GPPO", "WM-GPPO", "EA-noGES-GPPO", "EAWM-GPPO"))
    parser.add_argument("seed", type=int, choices=(1101, 2202, 3303))
    parser.add_argument("checkpoint")
    parser.add_argument("test_manifest")
    parser.add_argument("output_dir")
    parser.add_argument("--baseline-root", required=True)
    parser.add_argument("--world-checkpoint-dir", required=True)
    parser.add_argument("--expected-target-commit", required=True)
    parser.add_argument("--expected-checkpoint-sha256", required=True)
    parser.add_argument("--config", default=str(ROOT / "nodes" / "T-05" / "server-training-config.json"))
    args = parser.parse_args(argv)

    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    baseline_root = Path(args.baseline_root).resolve()
    checkpoint = Path(args.checkpoint).resolve()
    test_manifest = Path(args.test_manifest).resolve()
    output = Path(args.output_dir).resolve()
    if output.exists() and any(output.iterdir()):
        raise SystemExit("refusing to overwrite non-empty evaluation directory")
    output.mkdir(parents=True, exist_ok=True)
    if not torch.cuda.is_available():
        raise SystemExit("formal T-05 evaluation refuses to run without CUDA")
    if git(ROOT, "rev-parse", "HEAD") != args.expected_target_commit or git(ROOT, "status", "--porcelain"):
        raise SystemExit("target commit/worktree is not frozen")
    if git(baseline_root, "rev-parse", "HEAD") != config["baseline"]["commit"] or git(baseline_root, "status", "--porcelain"):
        raise SystemExit("baseline commit/worktree is not frozen")
    if sha256(checkpoint) != args.expected_checkpoint_sha256:
        raise SystemExit("policy checkpoint SHA-256 mismatch")

    sys.path.insert(0, str(baseline_root))
    import ppo_allocation.random_event.experiment as experiment  # noqa: PLC0415
    from ppo_allocation.random_event.baselines import GraphPolicyAdapter  # noqa: PLC0415
    from ppo_allocation.random_event.metrics import aggregate_tapes  # noqa: PLC0415
    from ppo_allocation.random_event.models import (  # noqa: PLC0415
        GraphActorCritic,
        GraphModelConfig,
    )
    from gppo_world.calibration import ShadowCalibration  # noqa: PLC0415
    from gppo_world.gppo_adapter import (  # noqa: PLC0415
        LatentAdapterConfig,
        LatentAugmentedActorCritic,
        LatentContextStore,
        freeze_world_model,
    )
    from gppo_world.gppo_shadow_env import (  # noqa: PLC0415
        PostActionShadowEnv,
        ensure_noop_action_compatibility,
    )
    from gppo_world.model import EventAwareGraphWorldModel  # noqa: PLC0415
    from gppo_world.shadow import ShadowRuntime  # noqa: PLC0415

    device = torch.device("cuda")
    created_envs: list[PostActionShadowEnv] = []
    original_env_class = experiment.RandomEventAllocationEnv
    world_runtime = None
    context_store = None

    def compatible_env_factory(*factory_args: Any, **factory_kwargs: Any):
        raw = original_env_class(*factory_args, **factory_kwargs)
        ensure_noop_action_compatibility(raw)
        return raw

    experiment.RandomEventAllocationEnv = compatible_env_factory

    if args.group == "GPPO":
        model, metadata = GraphActorCritic.load(checkpoint, map_location=device)
    else:
        def base_factory(spec: dict[str, Any]):
            return GraphActorCritic(
                spec["node_dims"],
                GraphModelConfig(**spec["config"]),
                edge_dims={
                    tuple(key.split("__")): int(value)
                    for key, value in spec["edge_dims"].items()
                },
            )

        model, metadata = LatentAugmentedActorCritic.load(
            checkpoint, base_factory=base_factory, map_location=device
        )
        world_seed = config["world_seed_by_training_seed"][str(args.seed)]
        world_name = config["groups"][args.group]["world_model_pattern"].format(
            world_seed=world_seed
        )
        world_path = Path(args.world_checkpoint_dir).resolve() / world_name
        if sha256(world_path) != config["world_checkpoint_sha256"][world_name]:
            raise SystemExit("world checkpoint SHA-256 mismatch")
        world_model, _ = EventAwareGraphWorldModel.load(world_path, map_location="cpu")
        freeze_world_model(world_model)
        model_identity = model.model_version or f"{world_name}:{sha256(world_path)}"
        context_store = LatentContextStore(
            LatentAdapterConfig(
                latent_dim=world_model.config.hidden_dim + world_model.config.stochastic_dim
            ),
            model_variant=args.group,
            model_version=model_identity,
        )
        model.context_store = context_store
        calibration_path = ROOT / config["shadow_calibration"]["path"]
        calibration = ShadowCalibration.from_dict(
            json.loads(calibration_path.read_text(encoding="utf-8"))
        )
        world_runtime = ShadowRuntime(
            world_model, calibration, model_version=model_identity
        )

        def wrapped_env_factory(*factory_args: Any, **factory_kwargs: Any):
            raw = compatible_env_factory(*factory_args, **factory_kwargs)
            wrapped = PostActionShadowEnv(
                raw, world_runtime, context_store, model_variant=args.group
            )
            created_envs.append(wrapped)
            return wrapped

        experiment.RandomEventAllocationEnv = wrapped_env_factory

    model.to(device)
    model.eval()
    policy = GraphPolicyAdapter(
        model=DeviceModelProxy(model, device),
        name=f"{args.group} seed={args.seed} step=50000",
    )
    manifest, tapes = experiment.load_tape_bank(test_manifest)
    expected_tapes = int(config["evaluation"]["held_out_test_tapes"])
    if len(tapes) != expected_tapes:
        raise SystemExit(f"held-out Test bank must contain exactly {expected_tapes} tapes")
    episodes = []
    trace_index = []
    try:
        for tape_id, tape in tapes:
            episode, trace = experiment.run_episode(
                policy,
                tape_id=tape_id,
                tape=tape,
                algorithm=args.group,
                max_decisions=100,
            )
            episodes.append(episode)
            trace_path = output / "traces" / f"{tape_id}.json"
            write_json(trace_path, trace)
            trace_index.append(
                {
                    "tape_id": tape_id,
                    "path": trace_path.relative_to(output).as_posix(),
                    "sha256": sha256(trace_path),
                }
            )
    finally:
        experiment.RandomEventAllocationEnv = original_env_class
    safety = {
        "shadow": None if world_runtime is None else world_runtime.counters,
        "environment_mutations": sum(env.audit().real_environment_mutation_count for env in created_envs),
        "belief_mutations": sum(env.audit().real_belief_mutation_count for env in created_envs),
        "action_mask_mutations": sum(env.audit().real_action_mask_mutation_count for env in created_envs),
        "version_mutations": sum(env.audit().real_version_mutation_count for env in created_envs),
        "action_submissions_by_shadow": 0 if world_runtime is None else world_runtime.counters["action_submission_count"],
    }
    if any(
        safety[key]
        for key in (
            "environment_mutations",
            "belief_mutations",
            "action_mask_mutations",
            "version_mutations",
            "action_submissions_by_shadow",
        )
    ):
        raise SystemExit("held-out evaluation detected a Shadow safety violation")
    result = {
        "format": "gppo-t05-heldout-evaluation/0.1.0",
        "group": args.group,
        "seed": args.seed,
        "checkpoint": checkpoint.name,
        "checkpoint_sha256": sha256(checkpoint),
        "test_manifest": str(test_manifest),
        "test_manifest_sha256": sha256(test_manifest),
        "tape_count": len(episodes),
        "summary": aggregate_tapes(episodes),
        "episode_records": [episode.to_dict() for episode in episodes],
        "trace_index": trace_index,
        "safety": safety,
        "checkpoint_metadata": metadata,
    }
    write_json(output / "evaluation.json", result)
    write_json(output / "trace-index.json", trace_index)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

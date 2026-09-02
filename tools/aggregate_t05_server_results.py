"""Aggregate the 12 fixed T-05 held-out results without selecting a winner."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

GROUPS = ("GPPO", "WM-GPPO", "EA-noGES-GPPO", "EAWM-GPPO")
SEEDS = (1101, 2202, 3303)
METRICS = (
    "event_success_rate",
    "recovery_delay",
    "cumulative_uncovered_time",
    "legal_coverage_rate",
    "final_infeasible_rate",
    "episode_return",
    "fixed_j",
    "repair_count",
    "inference_latency_ms",
)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("results_root")
    parser.add_argument("output")
    parser.add_argument("--baseline-root", required=True)
    args = parser.parse_args(argv)
    baseline_root = Path(args.baseline_root).resolve()
    sys.path.insert(0, str(baseline_root))
    from ppo_allocation.random_event.metrics import (  # noqa: PLC0415
        descriptive_statistics,
        paired_metric_report,
    )

    root = Path(args.results_root).resolve()
    paths = list(root.rglob("evaluation.json"))
    records: dict[tuple[str, int], dict[str, Any]] = {}
    for path in paths:
        value = json.loads(path.read_text(encoding="utf-8"))
        key = (str(value["group"]), int(value["seed"]))
        if key in records:
            raise SystemExit(f"duplicate evaluation for {key}")
        records[key] = value
    expected = {(group, seed) for group in GROUPS for seed in SEEDS}
    if set(records) != expected:
        missing = sorted(expected - set(records))
        extra = sorted(set(records) - expected)
        raise SystemExit(f"expected exactly 12 evaluations; missing={missing}, extra={extra}")
    manifest_hashes = {item["test_manifest_sha256"] for item in records.values()}
    if len(manifest_hashes) != 1 or any(item["tape_count"] != 100 for item in records.values()):
        raise SystemExit("all evaluations must use the same frozen 100-tape Test bank")
    for seed in SEEDS:
        reference_ids = [row["tape_id"] for row in records[("GPPO", seed)]["episode_records"]]
        for group in GROUPS:
            ids = [row["tape_id"] for row in records[(group, seed)]["episode_records"]]
            if ids != reference_ids:
                raise SystemExit(f"paired tape order mismatch for {group} seed {seed}")

    per_seed_effects: dict[str, Any] = {}
    for group in GROUPS[1:]:
        per_seed_effects[group] = {}
        for seed in SEEDS:
            candidate = records[(group, seed)]["episode_records"]
            control = records[("GPPO", seed)]["episode_records"]
            per_seed_effects[group][str(seed)] = {
                metric: paired_metric_report(
                    candidate,
                    control,
                    metric,
                    n_resamples=2000,
                    seed=20260902 + seed,
                )
                for metric in METRICS
            }

    seed_stability: dict[str, Any] = {}
    for group in GROUPS:
        seed_stability[group] = {}
        for metric in METRICS:
            values = []
            for seed in SEEDS:
                summary = records[(group, seed)]["summary"]["metrics"][metric]
                if summary["mean"] is not None:
                    values.append(float(summary["mean"]))
            seed_stability[group][metric] = descriptive_statistics(values)
    effect_stability: dict[str, Any] = {}
    for group in GROUPS[1:]:
        effect_stability[group] = {
            metric: descriptive_statistics(
                [
                    per_seed_effects[group][str(seed)][metric]["mean_difference"]
                    for seed in SEEDS
                    if per_seed_effects[group][str(seed)][metric]["mean_difference"] is not None
                ]
            )
            for metric in METRICS
        }

    safety = {
        "all_shadow_writes_zero": all(
            not any(
                item["safety"][key]
                for key in (
                    "environment_mutations",
                    "belief_mutations",
                    "action_mask_mutations",
                    "version_mutations",
                    "action_submissions_by_shadow",
                )
            )
            for item in records.values()
        ),
        "per_run": {
            f"{group}/seed{seed}": records[(group, seed)]["safety"]
            for group in GROUPS
            for seed in SEEDS
        },
    }
    result = {
        "format": "gppo-t05-four-group-ablation/0.1.0",
        "status": "evaluated_no_checkpoint_selection",
        "groups": list(GROUPS),
        "seeds": list(SEEDS),
        "test_manifest_sha256": next(iter(manifest_hashes)),
        "per_run_summaries": {
            f"{group}/seed{seed}": records[(group, seed)]["summary"]
            for group in GROUPS
            for seed in SEEDS
        },
        "paired_effects_candidate_minus_gppo": per_seed_effects,
        "seed_stability": seed_stability,
        "paired_effect_seed_stability": effect_stability,
        "safety": safety,
        "claim_rule": "A group-level benefit must be visible across independent seeds; a best-seed result is insufficient.",
    }
    if not safety["all_shadow_writes_zero"]:
        raise SystemExit("cannot aggregate: at least one safety counter is non-zero")
    write_json(Path(args.output).resolve(), result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

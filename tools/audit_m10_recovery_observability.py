"""Audit recovery observability and freeze a conditional opportunity curriculum.

This is a no-training diagnostic.  Candidate scenarios are generated into new
split-specific tapes, then executed by the existing public-information rule
controller through the unchanged M-10 environment, command, ACK, lease and
service gates.  The simulator's private state is used only to audit outcomes;
it is never passed to the controller.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
from typing import Any

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from gppo_world.m10_communication import weak_communication_profile
from gppo_world.m10_environment import (
    M10Config,
    M10Environment,
    M10Scenario,
    M10TaskSpec,
    scenario_from_dict,
    scenario_to_dict,
)
from gppo_world.service_clock import ServiceEvent
from tools.diagnose_m10_noop_capacity import deadline_distance_action
from tools.run_m10_r3 import load_policy
from gppo_world.m10_training import masked_distribution, _policy_input_bundle


SPLITS = ("recovery-opportunity-train", "recovery-opportunity-validation",
          "recovery-opportunity-test", "recovery-opportunity-ood")
LEVELS = ("recovery", "composite")
SEED_OFFSETS = {
    "recovery-opportunity-train": 91000,
    "recovery-opportunity-validation": 92000,
    "recovery-opportunity-test": 93000,
    "recovery-opportunity-ood": 94000,
}


def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str), encoding="utf-8")


def make_candidate(split: str, level: str, seed: int) -> M10Scenario:
    """Make one event-interrupted task with enough *potential* slack.

    This is a candidate, not yet a claimed opportunity.  The reference
    controller must still prove the complete public-information execution.
    The OOD split changes geometry, service and fault timing ranges while
    retaining the same one-event contract.
    """
    rng = np.random.default_rng(seed)
    ood = split.endswith("ood")
    distance = float(rng.uniform(0.9, 1.45) if not ood else rng.uniform(1.2, 1.9))
    service = float(rng.uniform(1.8, 2.7) if not ood else rng.uniform(2.2, 3.1))
    event_time = float(rng.uniform(2.05, 2.55) if not ood else rng.uniform(2.2, 2.85))
    # Ensure the affected UAV is in service at the event, not merely idle or
    # travelling.  The first command is accepted at t=0 and travel starts.
    event_time = max(event_time, distance + 0.20)
    deadline = float(rng.uniform(13.0, 15.0) if not ood else rng.uniform(15.0, 18.0))
    kind = "damage" if int(rng.integers(0, 2)) == 0 else "disconnect"
    events = [ServiceEvent(event_time, "uav-0", kind)]
    if kind == "disconnect":
        events.append(ServiceEvent(float(event_time + rng.uniform(4.0, 5.0)), "uav-0", "reconnect"))
    task = M10TaskSpec(
        task_id="task-0", arrival=0.0, x=distance, y=0.0, deadline=deadline,
        service=service, priority=1.5, region_id=0, target_id=0,
    )
    name = f"{level}-single-interruption"
    return M10Scenario(
        name=name, tasks=(task,), events=tuple(events), seed=seed,
        split=split, tape_id=f"{split}-{level}-seed-{seed}",
        communication=weak_communication_profile(level),
    )


def candidate_actions(obs: dict[str, Any], config: M10Config) -> list[int]:
    mask = np.asarray(obs["mask"], dtype=np.bool_)
    return [int(x) for x in np.flatnonzero(mask[:-1])]


def interrupted_task(scenario: M10Scenario, env: M10Environment) -> bool:
    for event in scenario.events:
        if event.kind not in {"damage", "disconnect"}:
            continue
        if any(row.get("resource") == event.resource and row.get("task") == "task-0"
               and row.get("kind") in {"travel", "service"}
               and abs(float(row.get("end", -1.0)) - event.time) < 1e-7
               for row in env.clock.log):
            return True
    return False


def fault_knowledge(scenario: M10Scenario, env: M10Environment) -> dict[str, Any] | None:
    event = next(event for event in scenario.events if event.kind in {"damage", "disconnect"})
    field = "alive" if event.kind == "damage" else "connected"
    rows = [row for row in env._communication_log
            if row.get("link") == "telemetry" and row.get("status") == "received"
            and row.get("entity") == event.resource and row.get("field") == field
            and float(row.get("measured_at", -1.0)) >= event.time - 1e-7]
    if not rows:
        return None
    return min(rows, key=lambda row: float(row.get("time", math.inf)))


def run_public_scheduler(scenario: M10Scenario, config: M10Config) -> dict[str, Any]:
    """Run the reference controller using only observation/mask/action APIs."""
    env = M10Environment(config, scenario)
    obs = env.reset()
    done = False
    rows: list[dict[str, Any]] = []
    active: set[int] = set()
    while not done and len(rows) < int(config.horizon / config.decision_interval) + 3:
        visible = candidate_actions(obs, config)
        if visible:
            action = deadline_distance_action(env, obs)
            submit = True
            control = "deadline_distance_priority"
        elif active:
            action = min(active)
            submit = False
            control = "continue_existing_leases"
        else:
            action = config.action_count - 1
            submit = True
            control = "public_noop"
        before = len(env.execution.log)
        obs, reward, done, info = env.step(action, submit_command=submit)
        rows.append({
            "step": len(rows), "time": float(info["time"]), "action": int(action),
            "submit": submit, "control": control,
            "candidate_actions_before": visible,
            "candidate_count_after": len(candidate_actions(obs, config)),
            "feedback": info["feedback"], "reward": float(reward),
            "accepted_delta": list(env.execution.log[before:]),
            "active_continuations": list(info.get("active_continuations", [])),
            "lease_renewals": dict(info.get("lease_renewals", {})),
        })
        active = {int(item["action"]) for item in info.get("active_continuations", [])}
    accepted = [row for row in env.execution.log if row.get("result") == "accepted"]
    event = next(event for event in scenario.events if event.kind in {"damage", "disconnect"})
    knowledge = fault_knowledge(scenario, env)
    post_event_service = [row for row in env.clock.log if row.get("kind") == "service"
                          and float(row.get("start", math.inf)) >= event.time - 1e-7]
    task = env.clock.tasks["task-0"]
    messages = env._communication_log
    counts: dict[str, int] = {}
    for row in messages:
        key = f"{row.get('link')}:{row.get('status')}"
        counts[key] = counts.get(key, 0) + 1
    return {
        "completed": task.state.value == "completed", "task_state": task.state.value,
        "task_service": float(task.service), "deadline": float(task.deadline),
        "interrupted": interrupted_task(scenario, env),
        "fault_knowledge": knowledge,
        "first_public_candidate_time": next((row["time"] for row in rows if row["candidate_count_after"] > 0), None),
        "first_task_accept_time": next((float(row["time"]) for row in rows
                                        if float(row["time"]) >= event.time - 1e-7
                                        and any(x.get("result") == "accepted"
                                               and env.execution.commands.get(x.get("command_id"), None) is not None
                                               and env.execution.commands[x["command_id"]].task_id == "task-0"
                                               and env.execution.commands[x["command_id"]].uav_id != event.resource
                                               for x in row["accepted_delta"])), None),
        "post_event_service_count": len(post_event_service),
        "accepted_commands": len(accepted), "rows": rows,
        "execution_log": list(env.execution.log),
        "clock_log": list(env.clock.log),
        "commands": {key: vars(value) for key, value in env.execution.commands.items()},
        "communication_counts": counts,
        "communication_log": list(messages),
        "audit": {"execution_log_entries": len(env.execution.log),
                   "security_rejections": [row for row in env.execution.log
                                            if row.get("result") in {"ack_identity", "fenced", "duplicate_or_empty_id", "unauthorized"}]},
    }


def audit_policy(checkpoint: Path, scenarios: list[M10Scenario], config: M10Config, device: str) -> dict[str, Any]:
    """Compact old-checkpoint re-evaluation; no gradients or parameter updates."""
    import torch
    policy, metadata = load_policy(checkpoint, config, device)
    device_obj = torch.device(device)
    results = []
    for scenario in scenarios:
        env = M10Environment(config, scenario)
        obs = env.reset()
        hidden = None
        last_action = None
        done = False
        trace = []
        while not done and len(trace) < int(config.horizon / config.decision_interval) + 3:
            vector, _, _, _ = _policy_input_bundle(env, obs, None, fusion="base",
                                                   device=device_obj, trigger_threshold=0.5)
            tensor = torch.tensor(vector, dtype=torch.float32, device=device_obj)[None, :]
            mask = torch.tensor(obs["mask"], dtype=torch.bool, device=device_obj)[None, :]
            logits, _, hidden = policy(tensor, hidden)
            dist = masked_distribution(logits, mask)
            action = int(torch.argmax(dist.logits, dim=-1).item())
            before = len(env.execution.log)
            obs, reward, done, info = env.step(action, submit_command=True)
            trace.append({"time": float(info["time"]), "action": action,
                          "candidate_count": int(np.asarray(mask[0, :-1].cpu()).sum()),
                          "feedback": info["feedback"],
                          "accepted_delta": list(env.execution.log[before:])})
        task = env.clock.tasks["task-0"]
        results.append({"tape_id": scenario.tape_id, "completed": task.state.value == "completed",
                        "task_state": task.state.value, "task_service": float(task.service),
                        "trace": trace, "communication_counts": _count_messages(env._communication_log),
                        "audit": {"execution_log_entries": len(env.execution.log),
                                  "security_rejections": [row for row in env.execution.log
                                                           if row.get("result") in {"ack_identity", "fenced", "duplicate_or_empty_id", "unauthorized"}]}})
    return {"checkpoint": str(checkpoint), "metadata": metadata, "episodes": results,
            "completed": sum(bool(row["completed"]) for row in results), "episodes_total": len(results)}


def _count_messages(rows: list[dict[str, Any]]) -> dict[str, int]:
    result: dict[str, int] = {}
    for row in rows:
        key = f"{row.get('link')}:{row.get('status')}"
        result[key] = result.get(key, 0) + 1
    return result


def summarize_training(root: Path) -> dict[str, Any]:
    result = {}
    for seed in (1101, 2203, 3307):
        path = root / "output" / "per-seed" / f"seed-{seed}.json"
        if not path.exists():
            result[str(seed)] = {"present": False}
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        records = payload.get("records", [])
        result[str(seed)] = {
            "present": True, "records": len(records),
            "levels": [row.get("level") for row in records],
            "environment_steps": payload.get("new_environment_steps"),
            "trajectory_export_present": any("transitions" in row or "rollout" in row for row in records),
            "validation_episode_exports": sum(len(row.get("metrics", {}).get("policy", {}).get("episodes", [])) for row in records),
            "statement": "training rollout/event-level recovery sample count is unknown; records are checkpoint validation evaluations",
        }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase2-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path)
    parser.add_argument("--pool-count", type=int, default=48)
    parser.add_argument("--selected-count", type=int, default=16)
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()
    if args.pool_count < args.selected_count or args.selected_count <= 0:
        raise SystemExit("pool-count must be >= positive selected-count")
    config = M10Config()
    args.output.mkdir(parents=True, exist_ok=True)
    all_selected: dict[str, list[M10Scenario]] = {}
    audit_rows: list[dict[str, Any]] = []
    for split in SPLITS:
        selected: list[M10Scenario] = []
        selected_by_level = {level: 0 for level in LEVELS}
        split_pool: list[dict[str, Any]] = []
        for level in LEVELS:
            for index in range(args.pool_count):
                seed = SEED_OFFSETS[split] + (0 if level == "recovery" else 10000) + index
                scenario = make_candidate(split, level, seed)
                run = run_public_scheduler(scenario, config)
                eligible = bool(run["interrupted"] and run["fault_knowledge"] is not None
                                and run["first_public_candidate_time"] is not None
                                and run["first_task_accept_time"] is not None
                                and run["post_event_service_count"] > 0
                                and run["completed"])
                row = {"split": split, "level": level, "seed": seed,
                       "tape_id": scenario.tape_id, "eligible": eligible,
                       "scenario": scenario_to_dict(scenario),
                       "reference": run}
                split_pool.append(row)
                audit_rows.append(row)
                per_level_target = args.selected_count // len(LEVELS) + (1 if LEVELS.index(level) < args.selected_count % len(LEVELS) else 0)
                if eligible and selected_by_level[level] < per_level_target:
                    selected.append(scenario)
                    selected_by_level[level] += 1
        if len(selected) < args.selected_count:
            raise SystemExit(f"{split}: only {len(selected)} eligible candidates; increase candidate pool explicitly")
        all_selected[split] = selected
        dump(args.output / "pool" / f"{split}.json", split_pool)
        dump(args.output / "tapes" / f"{split}.json", [scenario_to_dict(item) for item in selected])

    selected_flat = [s for values in all_selected.values() for s in values]
    policy_eval = None
    if args.checkpoint:
        policy_eval = audit_policy(args.checkpoint, selected_flat, config, args.device)
    by_split = {}
    for split in SPLITS:
        rows = [row for row in audit_rows if row["split"] == split]
        by_split[split] = {
            "pool": len(rows), "eligible": sum(bool(row["eligible"]) for row in rows),
            "selected": len(all_selected[split]),
            "selected_by_level": {level: sum(s.name.startswith(level) for s in all_selected[split]) for level in LEVELS},
            "filter_rate": 1.0 - sum(bool(row["eligible"]) for row in rows) / max(len(rows), 1),
            "selection_rule": "first eligible candidates in deterministic seed order; conditional curriculum, not pressure-distribution estimate",
        }
    protocol = {
        "format": "m10-recovery-observability/0.1.0",
        "training_started": False, "B_started": False, "C_started": False,
        "old_pressure_tape_modified": False, "final_test_used_for_selection": False,
        "controller": "existing public-information deadline/distance scheduler through unchanged gates",
        "profiles": list(LEVELS), "splits": list(SPLITS),
        "candidate_pool_count_per_split": args.pool_count * len(LEVELS),
        "selected_count_per_split": args.selected_count,
        "candidate_contract": {
            "one_interrupted_task": True,
            "fault": "damage or disconnect of uav-0 during travel/service",
            "legal_knowledge": "received post-fault telemetry only, measured_at >= event time",
            "public_candidate": "nonempty received-only action mask after knowledge",
            "reference_success": "accepted alternate command, post-event service, and completed before deadline",
            "private_truth": "only used after execution for audit; never input to controller",
        },
        "training_trajectory_statement": "phase2 per-seed artifacts export checkpoint validation episodes, not training rollout/event ledgers; training recovery sample count is unknown",
    }
    dump(args.output / "protocol.json", protocol)
    dump(args.output / "opportunity-audit.json", {
        "protocol": protocol, "training_artifact_audit": summarize_training(args.phase2_root),
        "by_split": by_split, "selected_tape_ids": {k: [s.tape_id for s in v] for k, v in all_selected.items()},
        "reference_selected_summary": {
            "episodes": len(selected_flat),
            "completed": sum(bool(row["eligible"]) for row in audit_rows if row["tape_id"] in {s.tape_id for s in selected_flat}),
            "note": "selected candidates are conditional on reference execution success; this is not an overall weak-communication success rate",
        },
        "old_policy": policy_eval,
        "full_pool": audit_rows,
    })
    print(json.dumps({"by_split": by_split, "training_recovery_samples": "unknown",
                      "selected": {k: len(v) for k, v in all_selected.items()},
                      "old_policy_completed": policy_eval["completed"] if policy_eval else None}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

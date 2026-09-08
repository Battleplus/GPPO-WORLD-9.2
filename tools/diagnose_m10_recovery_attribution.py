"""Attribute weak-communication recovery failures without training.

This diagnostic replays only the already-frozen phase-two composite validation
tape with the final A checkpoints and the legal public-information scheduler.
It records the observation/selection/transport/execution chain and keeps the
recovery denominator explicit.  It never reads a test tape and never changes
the environment contract.
"""

from __future__ import annotations

import argparse
import copy
from dataclasses import asdict
import json
from pathlib import Path
import sys
from typing import Any, Iterable

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from gppo_world.m10_environment import M10Config, M10Environment, M10Scenario, scenario_from_dict
from gppo_world.m10_training import _act, _policy_input_bundle
from tools.diagnose_m10_noop_capacity import deadline_distance_action, public_task_key
from tools.run_m10_r3 import load_policy


def dump(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, default=str), encoding="utf-8")


def task_slots(env: M10Environment) -> list[str]:
    return [str(item) for item in getattr(env.bridge.view, "_tasks", [])]


def visible_snapshot(env: M10Environment, obs: dict[str, Any]) -> dict[str, Any]:
    slots = task_slots(env)
    mask = np.asarray(obs["mask"], dtype=bool)
    candidates = []
    for action in np.flatnonzero(mask[:-1]):
        uav_index, task_index = divmod(int(action), env.config.task_capacity)
        if task_index < len(slots):
            candidates.append({"action": int(action), "uav_id": env.uav_ids[uav_index], "task_id": slots[task_index]})
    return {
        "time": float(obs["time"]),
        "version": int(obs["version"]),
        "task_slots": slots,
        "candidate_actions": candidates,
        "uav_public": [
            {field: {"value": float(row[index * 4]), "known": bool(row[index * 4 + 1]),
                     "valid": bool(row[index * 4 + 2]), "age": float(row[index * 4 + 3])}
             for index, field in enumerate(("x", "y", "energy", "alive", "connected", "idle"))}
            for row in np.asarray(obs["uavs"])
        ],
        "task_public": {
            slots[index]: {
                field: {"value": float(row[field_index * 4]), "known": bool(row[field_index * 4 + 1]),
                        "valid": bool(row[field_index * 4 + 2]), "age": float(row[field_index * 4 + 3])}
                for field_index, field in enumerate(("x", "y", "deadline", "remaining_service", "priority", "pending", "region_id", "target_id"))
            }
            for index, row in enumerate(np.asarray(obs["tasks"])) if index < len(slots)
        },
        "trigger_flags": dict(obs.get("trigger_flags", {})),
        "continuation_actions": [int(x) for x in obs.get("continuation_actions", ())],
    }


def offline_truth_snapshot(env: M10Environment) -> dict[str, Any]:
    """Diagnostics-only state; never passed to the actor or scheduler."""
    return {
        "resources": {uid: {"position": list(resource.position), "alive": bool(resource.alive),
                             "connected": bool(resource.connected), "energy": float(resource.energy)}
                      for uid, resource in env.clock.resources.items()},
        "tasks": {task_id: {"state": task.state.value, "service": float(task.service),
                             "assigned_uav": task.assigned_uav}
                  for task_id, task in env.clock.tasks.items()},
    }


def _active_action_set(info: dict[str, Any]) -> set[int]:
    return {int(item["action"]) for item in info.get("active_continuations", [])}


def replay_policy(policy: torch.nn.Module, scenario: M10Scenario, config: M10Config, device: str) -> dict[str, Any]:
    device_obj = torch.device(device)
    env = M10Environment(config, scenario)
    obs = env.reset()
    hidden = None
    done = False
    rows: list[dict[str, Any]] = []
    branch_snapshots: dict[int, tuple[M10Environment, dict[str, Any], torch.Tensor | None, float]] = {}
    total_reward = 0.0
    while not done and len(rows) < int(config.horizon / config.decision_interval) + 3:
        before = visible_snapshot(env, obs)
        vector, _, _, _ = _policy_input_bundle(env, obs, None, fusion="base", device=device_obj, trigger_threshold=0.5)
        action, _, _, hidden = _act(policy, vector, obs["mask"], hidden, device_obj, deterministic=True)
        before_exec = len(env.execution.log)
        truth_before = offline_truth_snapshot(env)
        obs, reward, done, info = env.step(action, submit_command=True)
        total_reward += float(reward)
        rows.append({
            "step": len(rows), "time_before": before["time"], "time": float(info["time"]),
            "controller": "policy", "action": int(action), "submit": True,
            "command_id": info.get("command_id"),
            "action_task": next((x["task_id"] for x in before["candidate_actions"] if x["action"] == action), None),
            "action_uav": next((x["uav_id"] for x in before["candidate_actions"] if x["action"] == action), None),
            "action_is_noop": action == config.action_count - 1,
            "before": before, "after": visible_snapshot(env, obs),
            "offline_truth_before": truth_before,
            "feedback": str(info["feedback"]), "counts": dict(info["counts"]),
            "new_events": list(info.get("new_events", [])),
            "execution_delta": list(env.execution.log[before_exec:]),
            "active_continuations": list(info.get("active_continuations", [])),
            "lease_renewals": dict(info.get("lease_renewals", {})),
            "communication_delta": list(info.get("communication_delta", [])),
            "reward": float(reward), "terminated": bool(info.get("terminated")),
            "truncated": bool(info.get("truncated")),
        })
        for event_index, event in enumerate(scenario.events):
            if event_index in branch_snapshots or event.kind not in {"damage", "disconnect"}:
                continue
            field = "alive" if event.kind == "damage" else "connected"
            if any(item.get("link") == "telemetry" and item.get("status") == "received"
                   and item.get("entity") == event.resource and item.get("field") == field
                   and item.get("measured_at") is not None
                   and float(item.get("measured_at")) >= float(event.time) - 1e-7
                   for item in info.get("communication_delta", [])):
                branch_snapshots[event_index] = (copy.deepcopy(env), copy.deepcopy(obs),
                                                 hidden.detach().clone() if hidden is not None else None,
                                                 float(info["time"]))
    payload = episode_payload(env, scenario, rows, total_reward)
    payload["_branch_snapshots"] = branch_snapshots
    return payload


def resume_reference(env: M10Environment, config: M10Config) -> dict[str, Any]:
    """Continue from an already-created state using only current public data."""
    obs = env._observation()
    active_actions = set(int(x) for x in getattr(env, "_active_actions", {}).values())
    rows: list[dict[str, Any]] = []
    total_reward = 0.0
    done = False
    while not done and len(rows) < int(config.horizon / config.decision_interval) + 3:
        before = visible_snapshot(env, obs)
        if before["candidate_actions"]:
            action, submit = deadline_distance_action(env, obs), True
        elif active_actions:
            action, submit = min(active_actions), False
        else:
            action, submit = config.action_count - 1, True
        before_exec = len(env.execution.log)
        obs, reward, done, info = env.step(action, submit_command=submit)
        total_reward += float(reward)
        rows.append({"time": float(info["time"]), "action": int(action), "submit": bool(submit),
                     "feedback": str(info["feedback"]), "execution_delta": list(env.execution.log[before_exec:]),
                     "active_continuations": list(info.get("active_continuations", [])),
                     "new_events": list(info.get("new_events", []))})
        active_actions = _active_action_set(info)
    return episode_payload(env, env.scenario, rows, total_reward)


@torch.no_grad()
def resume_policy(policy: torch.nn.Module, env: M10Environment, obs: dict[str, Any],
                  hidden: torch.Tensor | None, config: M10Config, device: str) -> dict[str, Any]:
    device_obj = torch.device(device)
    rows: list[dict[str, Any]] = []
    total_reward = 0.0
    done = False
    while not done and len(rows) < int(config.horizon / config.decision_interval) + 3:
        vector, _, _, _ = _policy_input_bundle(env, obs, None, fusion="base", device=device_obj, trigger_threshold=0.5)
        action, _, _, hidden = _act(policy, vector, obs["mask"], hidden, device_obj, deterministic=True)
        before_exec = len(env.execution.log)
        obs, reward, done, info = env.step(action, submit_command=True)
        total_reward += float(reward)
        rows.append({"time": float(info["time"]), "action": int(action), "submit": True,
                     "feedback": str(info["feedback"]), "execution_delta": list(env.execution.log[before_exec:]),
                     "active_continuations": list(info.get("active_continuations", [])),
                     "new_events": list(info.get("new_events", []))})
    return episode_payload(env, env.scenario, rows, total_reward)


def replay_reference(scenario: M10Scenario, config: M10Config) -> dict[str, Any]:
    env = M10Environment(config, scenario)
    obs = env.reset()
    active_actions: set[int] = set()
    done = False
    rows: list[dict[str, Any]] = []
    total_reward = 0.0
    while not done and len(rows) < int(config.horizon / config.decision_interval) + 3:
        before = visible_snapshot(env, obs)
        candidates = before["candidate_actions"]
        if candidates:
            action, submit, control = deadline_distance_action(env, obs), True, "deadline_distance_priority"
        elif active_actions:
            action, submit, control = min(active_actions), False, "continue_existing_leases"
        else:
            action, submit, control = config.action_count - 1, True, "no_visible_candidate"
        before_exec = len(env.execution.log)
        truth_before = offline_truth_snapshot(env)
        obs, reward, done, info = env.step(action, submit_command=submit)
        total_reward += float(reward)
        rows.append({
            "step": len(rows), "time_before": before["time"], "time": float(info["time"]),
            "controller": "legal_scheduler", "control": control, "action": int(action),
            "command_id": info.get("command_id"),
            "submit": bool(submit),
            "action_task": next((x["task_id"] for x in before["candidate_actions"] if x["action"] == action), None),
            "action_uav": next((x["uav_id"] for x in before["candidate_actions"] if x["action"] == action), None),
            "action_is_noop": action == config.action_count - 1, "before": before,
            "after": visible_snapshot(env, obs), "feedback": str(info["feedback"]),
            "offline_truth_before": truth_before,
            "counts": dict(info["counts"]), "new_events": list(info.get("new_events", [])),
            "execution_delta": list(env.execution.log[before_exec:]),
            "active_continuations": list(info.get("active_continuations", [])),
            "lease_renewals": dict(info.get("lease_renewals", {})),
            "communication_delta": list(info.get("communication_delta", [])),
            "reward": float(reward), "terminated": bool(info.get("terminated")),
            "truncated": bool(info.get("truncated")),
        })
        active_actions = _active_action_set(info)
    return episode_payload(env, scenario, rows, total_reward)


def episode_payload(env: M10Environment, scenario: M10Scenario, rows: list[dict[str, Any]], total_reward: float) -> dict[str, Any]:
    return {
        "tape_id": scenario.tape_id, "seed": scenario.seed, "rows": rows,
        "scenario_tasks": [asdict(task) for task in scenario.tasks],
        "completed": sum(task.state.value == "completed" for task in env.clock.tasks.values()),
        "expired": sum(task.state.value == "expired" for task in env.clock.tasks.values()),
        "return": float(total_reward), "execution_log": list(env.execution.log),
        "commands": {key: asdict(value) for key, value in env.execution.commands.items()},
        "clock_log": list(env.clock.log), "tasks": {
            key: {"state": value.state.value, "service": float(value.service), "deadline": float(value.deadline),
                  "completed_at": value.completed_at}
            for key, value in env.clock.tasks.items()
        },
        "communication_log": list(getattr(env, "_communication_log", [])),
    }


def interrupted_tasks(scenario: M10Scenario, episode: dict[str, Any]) -> list[dict[str, Any]]:
    """Build the denominator from an actual travel/service interval ending at the event."""
    result = []
    clock_log = episode.get("clock_log", [])
    for event in scenario.events:
        if event.kind not in {"damage", "disconnect"}:
            continue
        tasks = sorted({str(row["task"]) for row in clock_log
                        if row.get("kind") in {"travel", "service"}
                        and row.get("resource") == event.resource
                        and abs(float(row.get("end", -1.0)) - float(event.time)) <= 1e-7})
        for task_id in tasks:
            result.append({"tape_id": scenario.tape_id, "event_index": scenario.events.index(event),
                           "event": event.kind, "event_time": float(event.time),
                           "resource": event.resource, "task_id": task_id})
    return result


def first_fault_knowledge(episode: dict[str, Any], item: dict[str, Any]) -> dict[str, Any] | None:
    fields = {"damage": "alive", "disconnect": "connected"}
    field = fields[item["event"]]
    candidates = [row for row in episode.get("communication_log", [])
                  if row.get("link") == "telemetry" and row.get("status") == "received"
                  and row.get("entity") == item["resource"] and row.get("field") == field
                  # A delayed pre-fault sample is not legal knowledge of the
                  # fault.  The measured timestamp must be at/after the
                  # event; receipt can be later because of the tape.
                  and row.get("measured_at") is not None
                  and float(row.get("measured_at", -1.0)) >= item["event_time"] - 1e-7
                  and float(row.get("time", -1.0)) >= item["event_time"] - 1e-7]
    if not candidates:
        return None
    row = min(candidates, key=lambda x: float(x.get("time", 0.0)))
    return {"time": float(row["time"]), "message_id": row.get("message_id"),
            "measured_at": row.get("measured_at"), "received_at": row.get("received_at"),
            "field": field}


def command_rows(episode: dict[str, Any], task_id: str, after: float) -> list[dict[str, Any]]:
    commands = episode.get("commands", {})
    return [row for row in episode.get("execution_log", [])
            if float(row.get("time", -1.0)) >= after - 1e-7
            and row.get("result") in {"accepted", "awaiting_ack", "renewed", "inactive_lease", "lease_expired",
                                       "stale", "fenced", "masked"}
            and commands.get(row.get("command_id"), {}).get("task_id") == task_id]


def classify_pair(item: dict[str, Any], episode: dict[str, Any]) -> dict[str, Any]:
    knowledge = first_fault_knowledge(episode, item)
    rows = episode.get("rows", [])
    post = [row for row in rows if float(row["time"]) >= (knowledge["time"] if knowledge else item["event_time"]) - 1e-7]
    task_candidates = [candidate for row in post for candidate in row["before"]["candidate_actions"]
                       if candidate["task_id"] == item["task_id"]]
    selected = [row for row in post if row.get("action_task") == item["task_id"]
                and row.get("action_uav") != item["resource"] and row.get("submit")]
    accepted = []
    if knowledge:
        accepted = [row for row in command_rows(episode, item["task_id"], knowledge["time"])
                    if row.get("result") == "accepted"
                    and episode.get("commands", {}).get(row.get("command_id"), {}).get("uav_id") != item["resource"]]
    service_rows = [row for row in episode.get("clock_log", [])
                    if row.get("kind") == "service" and row.get("task") == item["task_id"]
                    and row.get("resource") != item["resource"] and float(row.get("start", 1e9)) >= item["event_time"] - 1e-7]
    final = episode.get("tasks", {}).get(item["task_id"], {})
    if knowledge is None:
        category = "not_legally_informed"
    elif not task_candidates:
        category = "known_but_no_public_legal_candidate"
    elif not selected:
        category = "candidate_visible_but_policy_did_not_select"
    elif not accepted:
        category = "command_or_ack_execution_rejected"
    elif not service_rows:
        accepted_time = min(float(row.get("time", item["event_time"])) for row in accepted)
        accepted_row = min((row for row in rows if float(row["time"]) >= accepted_time - 1e-7),
                           key=lambda row: float(row["time"]), default=None)
        spec = next((task for task in episode.get("scenario_tasks", []) if task.get("task_id") == item["task_id"]), None)
        resource_state = (accepted_row or {}).get("offline_truth_before", {}).get("resources", {})
        command = episode.get("commands", {}).get(accepted[0].get("command_id"), {})
        position = resource_state.get(command.get("uav_id"), {}).get("position")
        min_required = None
        if spec is not None and position is not None:
            distance = float(np.linalg.norm(np.asarray(position, dtype=float) - np.asarray([spec["x"], spec["y"]], dtype=float)))
            min_required = distance + float(spec["service"])
        deadline = float((final or {}).get("deadline", spec.get("deadline", 0.0) if spec else 0.0))
        accepted_ids = {row.get("command_id") for row in accepted}
        lease_failures = [row for row in command_rows(episode, item["task_id"], accepted_time)
                          if row.get("command_id") in accepted_ids
                          and row.get("result") in {"inactive_lease", "expired", "fenced"}]
        if min_required is not None and min_required > deadline - accepted_time + 1e-7:
            category = "accepted_but_physically_too_late"
        elif lease_failures:
            category = "accepted_but_lease_or_execution_interrupted"
        else:
            category = "accepted_but_no_post_event_service_unresolved"
    elif final.get("state") != "completed":
        category = "service_recovered_but_too_late_for_completion"
    else:
        category = "recovered_and_completed"
    no_candidate_reason = None
    if category == "known_but_no_public_legal_candidate":
        first = post[0] if post else None
        task = (first or {}).get("before", {}).get("task_public", {}).get(item["task_id"])
        uavs = (first or {}).get("before", {}).get("uav_public", [])
        if task is None:
            no_candidate_reason = "task_slot_not_visible"
        elif not all(task[field]["valid"] for field in ("x", "y", "deadline", "remaining_service", "priority", "pending")):
            no_candidate_reason = "task_required_telemetry_missing_or_stale"
        elif task["pending"]["value"] != 1 or task["remaining_service"]["value"] <= 0 or task["deadline"]["value"] <= float(first["time_before"]):
            no_candidate_reason = "task_not_pending_or_deadline_or_no_remaining_service"
        elif not any(all(uav[field]["valid"] and uav[field]["value"] == (1 if field in ("alive", "connected", "idle") else uav[field]["value"])
                        for field in ("x", "y", "energy", "alive", "connected", "idle")) and uav["energy"]["value"] > 0
                    for uav in uavs):
            no_candidate_reason = "no_publicly_eligible_uav"
        else:
            no_candidate_reason = "mask_or_execution_feasibility_unresolved"
    return {
        **item, "knowledge": knowledge, "candidate_count": len(task_candidates),
        "no_candidate_reason": no_candidate_reason,
        "candidate_examples": task_candidates[:12], "selected": selected[:12],
        "accepted": accepted[:12], "post_event_service": service_rows[:12],
        "final_task": final, "category": category,
    }


def compare_public_prefix(policy: dict[str, Any], reference: dict[str, Any], event_time: float) -> dict[str, Any]:
    p = [row["before"] for row in policy["rows"] if row["time_before"] <= event_time + 1e-7]
    r = [row["before"] for row in reference["rows"] if row["time_before"] <= event_time + 1e-7]
    return {"same_length": len(p) == len(r), "policy_steps": len(p), "reference_steps": len(r),
            "same_public_snapshots": p == r,
            "paired_from_episode_start": p == r}


def communication_audit(episodes: Iterable[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for episode in episodes:
        for row in episode.get("communication_log", []):
            key = f"{row.get('link')}:{row.get('status')}"
            counts[key] = counts.get(key, 0) + 1
    return {"counts": counts, "note": "status categories are nested by link and are not added as a single dropped total"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase2-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--max-episodes", type=int, default=64)
    args = parser.parse_args()
    root = args.phase2_root
    tape_rows = json.loads((root / "output" / "tapes" / "validation" / "composite.json").read_text(encoding="utf-8"))[:args.max_episodes]
    scenarios = [scenario_from_dict(row) for row in tape_rows]
    config = M10Config()
    seeds = (1101, 2203, 3307)
    all_cards = []
    reference_cards = []
    run_rows = []
    all_replays = []
    for seed in seeds:
        checkpoint = root / "output" / "checkpoints" / f"seed-{seed}" / "new-step-16384.pt"
        policy, metadata = load_policy(checkpoint, config, args.device)
        for scenario in scenarios:
            policy_ep = replay_policy(policy, scenario, config, args.device)
            reference_ep = replay_reference(scenario, config)
            cards = interrupted_tasks(scenario, policy_ep)
            policy_cards = [classify_pair(item, policy_ep) for item in cards]
            reference_opportunities = interrupted_tasks(scenario, reference_ep)
            ref_branch_cards = [classify_pair(item, reference_ep) for item in reference_opportunities]
            policy_side_reference_cards = [classify_pair(item, reference_ep) for item in cards]
            for pcard, rcard in zip(policy_cards, policy_side_reference_cards):
                pcard["seed"] = seed
                pcard["reference"] = rcard
                pcard["branch_comparison"] = compare_public_prefix(policy_ep, reference_ep, pcard["event_time"])
                snapshot = policy_ep.get("_branch_snapshots", {}).get(int(pcard["event_index"]))
                if snapshot is not None:
                    branch_env, branch_obs, branch_hidden, branch_time = snapshot
                    reference_env = copy.deepcopy(branch_env)
                    policy_env = copy.deepcopy(branch_env)
                    branch_reference = resume_reference(reference_env, config)
                    branch_policy = resume_policy(policy, policy_env, copy.deepcopy(branch_obs),
                                                  branch_hidden.clone() if branch_hidden is not None else None,
                                                  config, args.device)
                    target = pcard["task_id"]
                    pcard["same_state_branch"] = {
                        "available": True, "knowledge_boundary_time": branch_time,
                        "policy_final_state": branch_policy["tasks"].get(target, {}),
                        "reference_final_state": branch_reference["tasks"].get(target, {}),
                        "reference_completed": branch_reference["tasks"].get(target, {}).get("state") == "completed",
                        "reference_rows": branch_reference["rows"][:12],
                        "state_source": "policy_branch_at_first_legal_fault_telemetry",
                    }
                else:
                    pcard["same_state_branch"] = {"available": False,
                                                   "reason": "fault telemetry was not received at a decision boundary"}
                all_cards.append(pcard)
            for rcard in ref_branch_cards:
                rcard["seed"] = seed
                reference_cards.append(rcard)
            run_rows.append({"seed": seed, "tape_id": scenario.tape_id,
                             "policy": {k: policy_ep[k] for k in ("completed", "expired", "return")},
                             "reference": {k: reference_ep[k] for k in ("completed", "expired", "return")},
                             "policy_episode": policy_ep, "reference_episode": reference_ep,
                             "checkpoint_metadata": metadata})
            all_replays.extend((policy_ep, reference_ep))
            policy_ep.pop("_branch_snapshots", None)
    categories: dict[str, int] = {}
    for card in all_cards:
        categories[card["category"]] = categories.get(card["category"], 0) + 1
    reference_categories: dict[str, int] = {}
    for card in reference_cards:
        reference_categories[card["category"]] = reference_categories.get(card["category"], 0) + 1
    original_metrics = {}
    for seed in seeds:
        source = root / "output" / "per-seed" / f"seed-{seed}.json"
        payload = json.loads(source.read_text(encoding="utf-8"))
        final = payload["records"][-1]["metrics"]
        original_metrics[str(seed)] = final["recovery"]
    dump(args.output, {
        "protocol": "M-10 recovery attribution; no training; no test tape; deterministic episode-start replay",
        "source": {"phase2_root": str(root), "tape": "validation/composite.json", "seeds": list(seeds),
                   "checkpoint": "output/checkpoints/seed-{seed}/new-step-16384.pt"},
        "denominator": {"definition": "damage/disconnect event whose clock travel/service interval on the affected resource ends at the event, paired per interrupted task",
                         "original_stage2_metric": original_metrics,
                         "corrected_policy_opportunities": len(all_cards), "corrected_reference_opportunities": len(reference_cards),
                         "corrected_policy_recovered": sum(c["category"] == "recovered_and_completed" for c in all_cards),
                         "corrected_reference_recovered": sum(c["category"] == "recovered_and_completed" for c in reference_cards),
                         "policy_integer_categories": categories, "reference_integer_categories": reference_categories,
                         "not_recovery_opportunity": "events with no interrupted travel/service task are excluded, not deleted after policy failure"},
        "cards": all_cards,
        "reference_branch_cards": reference_cards,
        "episodes": run_rows,
        "communication_audit": communication_audit(all_replays),
        "limitations": [
            "policy/reference branches start from the same episode initial state and semantic-addressed tape, but are not claimed as state-identical after different actions",
            "event knowledge is inferred from received public fault telemetry; no simulator truth is fed to policy",
            "the reference scheduler is a diagnostic public-information controller, not an optimality proof",
            "no final test tape was read",
        ],
    })


if __name__ == "__main__":
    main()

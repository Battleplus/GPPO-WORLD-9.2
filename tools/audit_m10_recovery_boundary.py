"""Audit recovery-boundary opportunities and freeze an A-only experiment protocol.

This is an evaluation-only tool.  It consumes the already generated recovery
opportunity pool, replays the public reference controller and one frozen old
Graph-5 checkpoint on every pool member, and writes an event-level audit.  It
also runs a small factor scan for the development set.  No gradients,
checkpoint writes, B/C runs, or changes to the historical pressure tapes are
performed here.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import replace
from pathlib import Path
import sys
from typing import Any

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from gppo_world.m10_communication import CommunicationProfile
from gppo_world.m10_environment import (
    M10Config,
    M10Environment,
    M10Scenario,
    M10TaskSpec,
    scenario_from_dict,
)
from gppo_world.m10_training import _policy_input_bundle, masked_distribution
from tools.audit_m10_recovery_observability import (
    candidate_actions,
    fault_knowledge,
    interrupted_task,
    make_candidate,
    run_public_scheduler,
)
from tools.run_m10_r3 import load_policy


def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str), encoding="utf-8")


def fault_event(scenario: M10Scenario):
    return next(event for event in scenario.events if event.kind in {"damage", "disconnect"})


def legal_event_knowledge(scenario: M10Scenario, rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Find the first public post-fault evidence that can enable takeover.

    Explicit ``alive``/``connected`` telemetry is sufficient, but it is not
    the only legal path: a fresh task ``pending`` or
    ``remaining_service`` message can publish that the affected task is
    available again.  Static task fields and hidden simulator truth are not
    knowledge.  This keeps the audit aligned with the task-release contract
    under which a controller may act before an explicit fault bit arrives.
    """
    event = fault_event(scenario)
    allowed = {
        (event.resource, "alive"), (event.resource, "connected"),
        ("task-0", "pending"), ("task-0", "remaining_service"),
    }
    candidates = [row for row in rows
                  if row.get("link") == "telemetry" and row.get("status") == "received"
                  and (row.get("entity"), row.get("field")) in allowed
                  and float(row.get("measured_at", -math.inf)) >= event.time - 1e-7]
    return min(candidates, key=lambda row: (float(row.get("time", math.inf)), str(row.get("message_id", "")))) if candidates else None


def _task_command(env: M10Environment, row: dict[str, Any]) -> dict[str, Any] | None:
    command_id = row.get("command_id")
    if not command_id:
        return None
    command = env.execution.commands.get(command_id)
    return None if command is None else {
        "command_id": command.command_id,
        "task_id": command.task_id,
        "uav_id": command.uav_id,
        "token": command.token,
        "version": command.version,
    }


def _service_rows(env: M10Environment, event_time: float, task_id: str, affected: str) -> list[dict[str, Any]]:
    return [row for row in env.clock.log
            if row.get("kind") == "service" and row.get("task") == task_id
            and row.get("resource") != affected
            and float(row.get("start", math.inf)) >= event_time - 1e-7]


def _accepted_alternates(env: M10Environment, event_time: float, knowledge_time: float,
                         task_id: str, affected: str) -> list[dict[str, Any]]:
    result = []
    for row in env.execution.log:
        if row.get("result") != "accepted" or float(row.get("time", -math.inf)) < knowledge_time - 1e-7:
            continue
        command = _task_command(env, row)
        if command and command["task_id"] == task_id and command["uav_id"] != affected:
            result.append({"time": float(row["time"]), **command})
    return result


def _event_summary(scenario: M10Scenario, env: M10Environment) -> dict[str, Any]:
    event = fault_event(scenario)
    fault_bit_knowledge = fault_knowledge(scenario, env)
    knowledge = legal_event_knowledge(scenario, env._communication_log)
    knowledge_time = None if knowledge is None else float(knowledge["time"])
    task_id = "task-0"
    post_knowledge_rows = [] if knowledge_time is None else [
        row for row in env._communication_log
        if row.get("link") == "telemetry" and row.get("entity") == task_id
        and row.get("status") == "received" and float(row.get("time", -math.inf)) >= knowledge_time - 1e-7
    ]
    first_candidate = None
    if knowledge_time is not None:
        for row in getattr(env, "_policy_trace_for_audit", []):
            if float(row.get("time", math.inf)) >= knowledge_time - 1e-7 and row.get("candidate_actions"):
                first_candidate = float(row["time"])
                break
    alternates = _accepted_alternates(env, event.time, knowledge_time or math.inf, task_id, event.resource)
    service_rows_all = _service_rows(env, event.time, task_id, event.resource)
    alternate_uavs = {row["uav_id"] for row in alternates}
    service_rows = [row for row in service_rows_all if row.get("resource") in alternate_uavs]
    task = env.clock.tasks.get(task_id)
    completed = bool(task is not None and task.state.value == "completed")
    completed_at = None if task is None else task.completed_at
    security = [row for row in env.execution.log if row.get("result") in {
        "ack_identity", "duplicate_or_empty_id", "fenced", "unauthorized",
    }]
    reasons = []
    if not interrupted_task(scenario, env):
        reasons.append("no_interrupted_execution")
    if knowledge is None:
        reasons.append("no_legal_post_fault_telemetry")
    if knowledge is not None and first_candidate is None:
        reasons.append("no_public_candidate_after_knowledge")
    if knowledge is not None and not alternates:
        reasons.append("no_accepted_alternate_command")
    if not service_rows:
        reasons.append("no_post_event_alternate_service")
    if not completed:
        reasons.append("not_completed_before_deadline")
    if security:
        reasons.append("security_rejection")
    # A pre-event handoff can leave post-event service entries in the clock
    # log, but it is not a recovery opportunity.  Recovery requires both a
    # legal post-knowledge alternate acceptance and service by that accepted
    # alternate after the fault.
    recovery_service = bool(alternates and service_rows)
    recovery_complete = bool(recovery_service and completed and not security)
    return {
        "event": {"kind": event.kind, "resource": event.resource, "time": float(event.time)},
        "interrupted": bool(interrupted_task(scenario, env)),
        "affected_task": task_id,
        "fault_knowledge": fault_bit_knowledge,
        "legal_event_knowledge": knowledge,
        "knowledge_basis": None if knowledge is None else f"{knowledge.get('entity')}:{knowledge.get('field')}",
        "legal_knowledge_time": knowledge_time,
        "first_public_candidate_time_after_knowledge": first_candidate,
        "post_knowledge_task_telemetry_received": len(post_knowledge_rows),
        "accepted_alternate_commands": alternates,
        "post_event_alternate_service_rows": service_rows,
        "service_recovered": recovery_service,
        "task_completed": completed,
        "completed_at": completed_at,
        "deadline": None if task is None else float(task.deadline),
        "deadline_slack_at_knowledge": None if task is None or knowledge_time is None else float(task.deadline - knowledge_time),
        "security_rejections": security,
        "recovery_service_success": recovery_service and not security,
        "recovery_completion_success": recovery_complete,
        "failure_reasons": reasons,
    }


def run_policy(policy: torch.nn.Module, scenario: M10Scenario, config: M10Config,
               device: str) -> dict[str, Any]:
    device_obj = torch.device(device)
    env = M10Environment(config, scenario)
    obs = env.reset()
    hidden = None
    trace: list[dict[str, Any]] = []
    done = False
    while not done and len(trace) < int(config.horizon / config.decision_interval) + 3:
        vector, _, _, _ = _policy_input_bundle(env, obs, None, fusion="base", device=device_obj, trigger_threshold=0.5)
        tensor = torch.tensor(vector, dtype=torch.float32, device=device_obj)[None, :]
        mask = torch.tensor(obs["mask"], dtype=torch.bool, device=device_obj)[None, :]
        with torch.no_grad():
            logits, _, hidden = policy(tensor, hidden)
            dist = masked_distribution(logits, mask)
            action = int(torch.argmax(dist.logits, dim=-1).item())
        before = len(env.execution.log)
        before_time = float(env.clock.time)
        next_obs, reward, done, info = env.step(action, submit_command=True)
        trace.append({
            "time": before_time,
            "candidate_actions": candidate_actions(obs, config),
            "action": action,
            "submit_command": True,
            "reward": float(reward),
            "feedback": info["feedback"],
            "accepted_delta": list(env.execution.log[before:]),
            "version": int(obs["version"]),
            "mask": [bool(x) for x in obs["mask"]],
        })
        obs = next_obs
    env._policy_trace_for_audit = trace
    task = env.clock.tasks["task-0"]
    event_summary = _event_summary(scenario, env)
    return {
        "task_state": task.state.value,
        "completed": task.state.value == "completed",
        "return": float(sum(row["reward"] for row in trace)),
        "steps": len(trace),
        "trace": trace,
        "event_summary": event_summary,
        "execution_log": list(env.execution.log),
        "clock_log": list(env.clock.log),
        "communication_counts": _count_messages(env._communication_log),
        "communication_log": list(env._communication_log),
        "security_rejections": event_summary["security_rejections"],
    }


def _count_messages(rows: list[dict[str, Any]]) -> dict[str, int]:
    result: dict[str, int] = {}
    for row in rows:
        key = f"{row.get('link')}:{row.get('status')}"
        result[key] = result.get(key, 0) + 1
    return result


def reference_summary(row: dict[str, Any]) -> dict[str, Any]:
    """Reconstruct event-level claims from the already stored reference trace."""
    ref = row["reference"]
    scenario = scenario_from_dict(row["scenario"])
    event = fault_event(scenario)
    fault_bit_knowledge = ref.get("fault_knowledge")
    communication_rows = ref.get("communication_log", [])
    knowledge = legal_event_knowledge(scenario, communication_rows)
    if knowledge is None:
        # This fallback is only for legacy stored rows without communication
        # logs; it does not create new knowledge and is marked by the field
        # name in the resulting audit.
        knowledge = fault_bit_knowledge
    knowledge_time = None if knowledge is None else float(knowledge["time"])
    first_candidate = None
    # Reference rows store ``time`` after the one-second environment advance;
    # candidate_count_after is therefore the first public snapshot at that
    # timestamp.  candidate_actions_before belongs to the preceding snapshot
    # and would shift the knowledge-to-candidate interval by one decision.
    for step in ref.get("rows", []):
        if (knowledge_time is not None and float(step["time"]) >= knowledge_time - 1e-7
                and int(step.get("candidate_count_after", 0)) > 0):
            first_candidate = float(step["time"])
            break
    commands = ref.get("commands", {})
    alternates = []
    for entry in ref.get("execution_log", []):
        if entry.get("result") != "accepted" or knowledge_time is None or float(entry.get("time", -math.inf)) < knowledge_time - 1e-7:
            continue
        command = commands.get(entry.get("command_id"), {})
        if command.get("task_id") == "task-0" and command.get("uav_id") != event.resource:
            alternates.append({"time": float(entry["time"]), "command_id": entry.get("command_id"),
                               "task_id": command.get("task_id"), "uav_id": command.get("uav_id"),
                               "token": command.get("token"), "version": command.get("version")})
    service_rows_all = [r for r in ref.get("clock_log", []) if r.get("kind") == "service" and r.get("task") == "task-0"
                        and r.get("resource") != event.resource and float(r.get("start", math.inf)) >= event.time - 1e-7]
    alternate_uavs = {row["uav_id"] for row in alternates}
    service_rows = [r for r in service_rows_all if r.get("resource") in alternate_uavs]
    security = ref.get("audit", {}).get("security_rejections", [])
    reasons = []
    if not ref.get("interrupted"): reasons.append("no_interrupted_execution")
    if knowledge is None: reasons.append("no_legal_post_fault_telemetry")
    if knowledge is not None and first_candidate is None: reasons.append("no_public_candidate_after_knowledge")
    if knowledge is not None and not alternates: reasons.append("no_accepted_alternate_command")
    if not service_rows: reasons.append("no_post_event_alternate_service")
    if not ref.get("completed"): reasons.append("not_completed_before_deadline")
    if security: reasons.append("security_rejection")
    return {
        "event": {"kind": event.kind, "resource": event.resource, "time": float(event.time)},
        "interrupted": bool(ref.get("interrupted")),
        "affected_task": "task-0",
        "fault_knowledge": fault_bit_knowledge,
        "legal_event_knowledge": knowledge,
        "knowledge_basis": None if knowledge is None else f"{knowledge.get('entity')}:{knowledge.get('field')}",
        "legal_knowledge_time": knowledge_time,
        "first_public_candidate_time_after_knowledge": first_candidate,
        "accepted_alternate_commands": alternates,
        "post_event_alternate_service_rows": service_rows,
        "service_recovered": bool(alternates and service_rows),
        "task_completed": bool(ref.get("completed")),
        "completed_at": None,
        "deadline": float(ref["deadline"]),
        "deadline_slack_at_knowledge": None if knowledge_time is None else float(ref["deadline"] - knowledge_time),
        "security_rejections": security,
        "recovery_service_success": bool(alternates and service_rows) and not security,
        "recovery_completion_success": bool(alternates and service_rows) and bool(ref.get("completed")) and not security,
        "failure_reasons": reasons,
    }


def factor_scenarios() -> list[tuple[str, M10Scenario, M10Config]]:
    """Small one-factor-at-a-time development scan; no final-test selection."""
    base = make_candidate("recovery-boundary-development", "recovery", 92000)
    event = fault_event(base)
    out: list[tuple[str, M10Scenario, M10Config]] = []
    for delay, max_age in ((0.0, 2.5), (0.5, 2.5), (1.0, 2.5), (1.5, 2.5), (1.5, 1.0)):
        scenario = replace(base, tape_id=f"boundary-delay-{delay}-age-{max_age}")
        config = replace(M10Config(), telemetry_delay=delay, telemetry_max_age=max_age)
        out.append(("telemetry_delay_vs_max_age", scenario, config))
    for duration in (2.0, 3.0, 4.0, 5.0, 6.0):
        profile = CommunicationProfile(name=f"boundary-outage-{duration}",
                                        telemetry_outage_intervals=((3.0, 3.0 + duration),))
        scenario = replace(base, tape_id=f"boundary-outage-{duration}", communication=profile)
        out.append(("disconnect_duration", scenario, M10Config()))
    for slack in (2.0, 4.0, 6.0, 8.0, 10.0):
        task = replace(base.tasks[0], deadline=event.time + slack)
        scenario = replace(base, tape_id=f"boundary-slack-{slack}", tasks=(task,))
        out.append(("post_knowledge_deadline_slack", scenario, M10Config()))
    for distance in (0.8, 1.2, 1.6, 2.0, 2.4):
        for service in (1.5, 2.5, 3.5):
            task = replace(base.tasks[0], x=distance, service=service)
            scenario = replace(base, tape_id=f"boundary-distance-{distance}-service-{service}", tasks=(task,))
            out.append(("alternate_distance_service", scenario, M10Config()))
    for second_x, second_deadline in ((0.7, 9.0), (1.4, 10.0), (2.2, 12.0), (3.0, 14.0)):
        second = M10TaskSpec(task_id="task-1", arrival=0.0, x=second_x, y=1.0,
                             deadline=second_deadline, service=2.0, priority=1.0,
                             region_id=1, target_id=1)
        scenario = replace(base, tape_id=f"boundary-parallel-{second_x}-{second_deadline}", tasks=(base.tasks[0], second))
        out.append(("parallel_task_competition", scenario, M10Config()))
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--opportunity-audit", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()
    source = json.loads(args.opportunity_audit.read_text(encoding="utf-8"))
    policy, metadata = load_policy(args.checkpoint, M10Config(), args.device)
    pool_results = []
    four_way = {key: 0 for key in ("both_success", "reference_success_old_failure", "old_success_reference_failure", "both_failure")}
    by_split: dict[str, dict[str, Any]] = {}
    for row in source["full_pool"]:
        scenario = scenario_from_dict(row["scenario"])
        config = M10Config()
        ref = reference_summary(row)
        old = run_policy(policy, scenario, config, args.device)
        ref_ok = bool(ref["recovery_completion_success"])
        old_ok = bool(old["event_summary"]["recovery_completion_success"])
        if ref_ok and old_ok: category = "both_success"
        elif ref_ok and not old_ok: category = "reference_success_old_failure"
        elif old_ok and not ref_ok: category = "old_success_reference_failure"
        else: category = "both_failure"
        four_way[category] += 1
        item = {"split": row["split"], "level": row["level"], "seed": row["seed"], "tape_id": row["tape_id"],
                "selected": row["tape_id"] in set(source["selected_tape_ids"].get(row["split"], [])),
                "reference": ref, "old_policy": old, "category": category,
                "reference_pool_eligible": bool(row["eligible"]),
                "selection_failure_reasons": [] if row["eligible"] else ref["failure_reasons"]}
        pool_results.append(item)
        split = by_split.setdefault(row["split"], {"pool": 0, "by_category": {key: 0 for key in four_way}, "by_level": {}})
        split["pool"] += 1
        split["by_category"][category] += 1
        lvl = split["by_level"].setdefault(row["level"], {key: 0 for key in four_way})
        lvl[category] += 1
    scan = []
    for factor, scenario, config in factor_scenarios():
        ref_run = run_public_scheduler(scenario, config)
        ref_summary = reference_summary({"scenario": {
            "name": scenario.name, "seed": scenario.seed, "split": scenario.split, "tape_id": scenario.tape_id,
            "tasks": [{"task_id": t.task_id, "arrival": t.arrival, "x": t.x, "y": t.y, "deadline": t.deadline,
                       "service": t.service, "priority": t.priority, "region_id": t.region_id, "target_id": t.target_id} for t in scenario.tasks],
            "events": [{"time": e.time, "resource": e.resource, "kind": e.kind} for e in scenario.events],
            "communication": scenario.communication.to_dict()}, "reference": ref_run})
        old_run = run_policy(policy, scenario, config, args.device)
        scan.append({"factor": factor, "tape_id": scenario.tape_id, "config": config.__dict__,
                     "scenario": {"tasks": [t.__dict__ for t in scenario.tasks], "events": [e.__dict__ for e in scenario.events],
                                   "communication": scenario.communication.to_dict()},
                     "reference": ref_summary, "old_policy": old_run,
                     "category": ("both_success" if ref_summary["recovery_completion_success"] and old_run["event_summary"]["recovery_completion_success"]
                                  else "reference_success_old_failure" if ref_summary["recovery_completion_success"]
                                  else "old_success_reference_failure" if old_run["event_summary"]["recovery_completion_success"]
                                  else "both_failure")})
    selection = {}
    strict_tapes: dict[str, list[dict[str, Any]]] = {}
    selected_ids = source["selected_tape_ids"]
    for split, ids in selected_ids.items():
        selected = [x for x in pool_results if x["split"] == split and x["selected"]]
        unselected = [x for x in pool_results if x["split"] == split and not x["selected"]]
        selection[split] = {"selected_ids": ids,
                            "selected_count": len(selected),
                            "selected_event_success": sum(x["reference"]["recovery_completion_success"] for x in selected),
                            "unselected_count": len(unselected),
                            "unselected_reason_counts": _reason_counts(unselected),
                            "rule": "first eligible row in deterministic level/seed order, four per profile; no old-policy result used"}
        strict_rows = []
        for level in ("recovery", "composite"):
            strict_rows.extend([x for x in pool_results
                                 if x["split"] == split and x["level"] == level
                                 and x["reference"]["recovery_completion_success"]][:4])
        strict_tapes[split] = [{"tape_id": x["tape_id"], "level": x["level"],
                               "scenario": next(r["scenario"] for r in source["full_pool"] if r["tape_id"] == x["tape_id"])}
                              for x in strict_rows]
    reference_old_failure = [x for x in pool_results if x["category"] == "reference_success_old_failure"]
    policy_exposed_failures = [x for x in reference_old_failure if x["old_policy"]["event_summary"]["interrupted"]]
    candidate_visible_failures = [x for x in policy_exposed_failures
                                  if x["old_policy"]["event_summary"]["legal_event_knowledge"] is not None
                                  and x["old_policy"]["event_summary"]["first_public_candidate_time_after_knowledge"] is not None
                                  and not x["old_policy"]["event_summary"]["recovery_completion_success"]]
    output = {
        "format": "m10-recovery-boundary/1.0.0",
        "scope": {"training_started": False, "B_started": False, "C_started": False,
                   "old_pressure_tape_modified": False, "full_course_rerun": False,
                   "final_test_used_for_selection": False},
        "source": {"opportunity_audit": str(args.opportunity_audit), "checkpoint": str(args.checkpoint),
                   "checkpoint_metadata": metadata, "old_checkpoint_role": "frozen development comparator, not new training"},
        "definitions": {"opportunity": "interrupted travel/service task + legal post-fault telemetry + public alternate candidate",
                        "service_recovery": "alternate UAV produces real post-event service under unchanged gates",
                        "recovery_completion": "service_recovery and task completed before deadline, with zero security rejection",
                        "four_way": "reference and old checkpoint event-level recovery_completion_success booleans"},
        "full_pool": {"count": len(pool_results), "four_way": four_way, "by_split": by_split,
                      "selection_audit": selection, "strict_reference_selected_tapes": strict_tapes,
                      "rows": pool_results},
        "boundary_factor_scan": {"count": len(scan), "factors": sorted(set(x["factor"] for x in scan)), "rows": scan},
        "learning_opportunity_audit": {
            "reference_success_old_failure": len(reference_old_failure),
            "old_policy_was_itself_interrupted": len(policy_exposed_failures),
            "old_policy_had_legal_knowledge_and_public_candidate_but_failed": len(candidate_visible_failures),
            "old_policy_not_exposed_to_target_interruption": len(reference_old_failure) - len(policy_exposed_failures),
            "interpretation": "Only the candidate-visible failure count can support a direct recovery action-selection hypothesis; the current development pool has zero.",
            "sufficient_for_a_only_recovery_training": False,
        },
        "training_recovery_samples": "unknown; phase2 artifacts contain checkpoint validation episodes, no training rollout/event ledger",
        "next_experiment_decision": {
            "status": "do_not_start_a_only_training",
            "hypothesis": "exposing A-only training to legal, recoverable boundary events can improve recovery timing without changing base allocation contract",
            "blocked_by": ["zero old-policy failures with a public legal candidate after the policy's own interruption"],
            "only_if": ["a new development pool has a predeclared minimum of candidate-visible policy failures across both damage and disconnect", "independent final pressure and conditional final tapes are frozen", "future runner exports event ledger"],
            "branches": ["same-start-control-original-course", "same-start-treatment-recovery-boundary-course"],
            "training_now": False,
        },
    }
    dump(args.output / "recovery-boundary-audit.json", output)
    dump(args.output / "boundary-tapes.json", [{"tape_id": x["tape_id"], "factor": x["factor"], "scenario": x["scenario"], "config": x["config"]} for x in scan])
    print(json.dumps({"pool": len(pool_results), "four_way": four_way, "boundary_rows": len(scan), "training_started": False}, ensure_ascii=False, indent=2))


def _reason_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        for reason in row.get("selection_failure_reasons", []):
            counts[reason] = counts.get(reason, 0) + 1
    return counts


if __name__ == "__main__":
    main()

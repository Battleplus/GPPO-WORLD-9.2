"""Produce compact field/message evidence for the 37 stale-task cases.

Targeted replay only: the frozen phase-two composite validation tape and the
existing checkpoints are read; no training or final-test data is used.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
from typing import Any

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from gppo_world.m10_environment import M10Config, scenario_from_dict
from tools.diagnose_m10_recovery_attribution import (
    classify_pair,
    interrupted_tasks,
    replay_policy,
)
from tools.run_m10_r3 import load_policy


FIELDS = ("x", "y", "deadline", "remaining_service", "priority", "pending", "region_id", "target_id")
STATIC = {"x", "y", "region_id", "target_id"}
DYNAMIC = set(FIELDS) - STATIC


def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str), encoding="utf-8")


def message_status(rows: list[dict[str, Any]], task_id: str, event_time: float,
                   until: float | None = None) -> dict[str, dict[str, int]]:
    out: dict[str, dict[str, int]] = {field: {} for field in FIELDS}
    for row in rows:
        if row.get("link") != "telemetry" or row.get("entity") != task_id:
            continue
        if float(row.get("time", -1.0)) < event_time - 1e-7:
            continue
        if until is not None and float(row.get("time", math.inf)) > until + 1e-7:
            continue
        field = str(row.get("field"))
        if field not in out:
            continue
        status = str(row.get("status"))
        out[field][status] = out[field].get(status, 0) + 1
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase2-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--max-episodes", type=int, default=64)
    args = parser.parse_args()
    root = args.phase2_root
    tape = json.loads((root / "output" / "tapes" / "validation" / "composite.json").read_text(encoding="utf-8"))[:args.max_episodes]
    config = M10Config()
    details: list[dict[str, Any]] = []
    for seed in (1101, 2203, 3307):
        checkpoint = root / "output" / "checkpoints" / f"seed-{seed}" / "new-step-16384.pt"
        policy, metadata = load_policy(checkpoint, config, args.device)
        for payload in tape:
            scenario = scenario_from_dict(payload)
            episode = replay_policy(policy, scenario, config, args.device)
            for item in interrupted_tasks(scenario, episode):
                card = classify_pair(item, episode)
                if card.get("no_candidate_reason") != "task_required_telemetry_missing_or_stale":
                    continue
                knowledge = card.get("knowledge")
                boundary = None
                if knowledge is not None:
                    boundary = next((row["before"] for row in episode["rows"]
                                     if float(row["before"]["time"]) >= float(knowledge["time"]) - 1e-7), None)
                public = (boundary or {}).get("task_public", {}).get(item["task_id"], {})
                field_evidence = {
                    field: {"known": bool(public.get(field, {}).get("known", False)),
                            "valid": bool(public.get(field, {}).get("valid", False)),
                            "age": public.get(field, {}).get("age")}
                    for field in FIELDS
                }
                missing = [field for field, evidence in field_evidence.items() if not evidence["known"]]
                stale = [field for field, evidence in field_evidence.items()
                         if evidence["known"] and not evidence["valid"]]
                all_messages = [entry for row in episode["rows"] for entry in row.get("communication_delta", [])]
                boundary_time = (boundary or {}).get("time")
                statuses = message_status(all_messages, item["task_id"], item["event_time"], boundary_time)
                remaining_deadline = None
                if public.get("deadline", {}).get("known"):
                    remaining_deadline = float(public["deadline"]["value"]) - float((boundary or {}).get("time", 0.0))
                details.append({
                    "seed": seed, "tape_id": item["tape_id"], "event_index": item["event_index"],
                    "event": item["event"], "event_time": item["event_time"], "resource": item["resource"],
                    "task_id": item["task_id"], "knowledge": knowledge,
                    "knowledge_boundary_time": boundary_time,
                    "remaining_deadline_from_boundary": remaining_deadline,
                    "missing_fields": missing, "stale_fields": stale,
                    "static_missing": sorted(set(missing) & STATIC),
                    "dynamic_missing_or_stale": sorted((set(missing) | set(stale)) & DYNAMIC),
                    "task_public_at_boundary": field_evidence,
                    "message_status_after_event": statuses,
                    "publisher": "M10Environment._deliver_observations broadcasts task fields from simulator/controller-side observation path; not from affected UAV",
                    "publisher_source_contract": "gppo_world/m10_environment.py::_deliver_observations",
                    "final_task": card.get("final_task"),
                })
    dump(args.output, {
        "protocol": "M-10 observability detail; targeted replay only; no training; validation composite only",
        "checkpoint": "new-step-16384.pt", "seeds": [1101, 2203, 3307],
        "records": details, "record_count": len(details),
        "classification_note": "field evidence is observed at the first decision boundary after legal fault telemetry; static/dynamic labels describe the missing public fields, not an unproven implementation fault",
        "training_trajectory_statement": "phase2 artifacts contain checkpoint validation episodes but no training rollout/event ledger; training recovery opportunity/sample count remains unknown",
    })
    print(json.dumps({"record_count": len(details),
                      "static_missing": sum(bool(x["static_missing"]) for x in details),
                      "dynamic_missing_or_stale": sum(bool(x["dynamic_missing_or_stale"]) for x in details)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

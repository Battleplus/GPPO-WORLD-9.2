import json
from pathlib import Path

from tools.audit_m10_recovery_boundary import factor_scenarios, reference_summary


def test_reference_candidate_time_uses_post_step_snapshot_time():
    row = {
        "scenario": {
            "name": "recovery-single-interruption", "seed": 1,
            "split": "test", "tape_id": "tape-1",
            "tasks": [{"task_id": "task-0", "arrival": 0.0, "x": 1.0, "y": 0.0,
                        "deadline": 12.0, "service": 2.0, "priority": 1.0,
                        "region_id": 0, "target_id": 0}],
            "events": [{"time": 2.3, "resource": "uav-0", "kind": "damage"}],
            "communication": {"name": "ideal"},
        },
        "reference": {
            "fault_knowledge": {"time": 6.0, "measured_at": 6.0, "field": "alive"},
            "interrupted": True, "completed": True, "deadline": 12.0,
            "rows": [{"time": 6.0, "candidate_actions_before": [], "candidate_count_after": 2}],
            "execution_log": [{"time": 6.0, "result": "accepted", "command_id": "c1"}],
            "commands": {"c1": {"task_id": "task-0", "uav_id": "uav-1", "token": 2, "version": 4}},
            "clock_log": [{"kind": "service", "task": "task-0", "resource": "uav-1", "start": 6.5}],
            "audit": {"security_rejections": []},
        },
    }
    summary = reference_summary(row)
    assert summary["legal_knowledge_time"] == 6.0
    assert summary["first_public_candidate_time_after_knowledge"] == 6.0
    assert summary["recovery_service_success"] is True
    assert summary["recovery_completion_success"] is True


def test_pre_knowledge_handoff_is_not_recovery():
    row = {
        "scenario": {
            "name": "recovery-single-interruption", "seed": 2,
            "split": "test", "tape_id": "tape-2",
            "tasks": [{"task_id": "task-0", "arrival": 0.0, "x": 1.0, "y": 0.0,
                        "deadline": 12.0, "service": 2.0, "priority": 1.0,
                        "region_id": 0, "target_id": 0}],
            "events": [{"time": 2.3, "resource": "uav-0", "kind": "damage"}],
            "communication": {"name": "ideal"},
        },
        "reference": {
            "fault_knowledge": {"time": 6.0, "measured_at": 6.0, "field": "alive"},
            "interrupted": True, "completed": True, "deadline": 12.0,
            "rows": [{"time": 6.0, "candidate_actions_before": [], "candidate_count_after": 0}],
            "execution_log": [{"time": 3.0, "result": "accepted", "command_id": "c1"}],
            "commands": {"c1": {"task_id": "task-0", "uav_id": "uav-1", "token": 2, "version": 4}},
            "clock_log": [{"kind": "service", "task": "task-0", "resource": "uav-1", "start": 6.5}],
            "audit": {"security_rejections": []},
        },
    }
    summary = reference_summary(row)
    assert summary["accepted_alternate_commands"] == []
    assert summary["recovery_service_success"] is False
    assert "no_accepted_alternate_command" in summary["failure_reasons"]


def test_boundary_scan_covers_required_factors():
    factors = {factor for factor, _, _ in factor_scenarios()}
    assert factors == {
        "telemetry_delay_vs_max_age",
        "disconnect_duration",
        "post_knowledge_deadline_slack",
        "alternate_distance_service",
        "parallel_task_competition",
    }


def test_previous_observability_artifact_is_read_only_input():
    path = Path("m10-recovery-observability-v3/opportunity-audit.json")
    if path.exists():
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["protocol"]["old_pressure_tape_modified"] is False
        assert payload["protocol"]["training_started"] is False

from types import SimpleNamespace

from gppo_world.service_clock import ServiceEvent
from tools.diagnose_m10_recovery_attribution import (
    classify_pair,
    communication_audit,
    first_fault_knowledge,
    interrupted_tasks,
)


def _scenario():
    return SimpleNamespace(
        tape_id="validation-recovery-1",
        events=(ServiceEvent(4.0, "uav-0", "disconnect"),),
        tasks=(),
    )


def test_denominator_counts_interrupted_task_without_handoff():
    scenario = _scenario()
    episode = {"clock_log": [{"kind": "service", "resource": "uav-0", "task": "task-0",
                               "start": 3.0, "end": 4.0}]}
    assert interrupted_tasks(scenario, episode) == [{
        "tape_id": "validation-recovery-1", "event_index": 0, "event": "disconnect", "event_time": 4.0,
        "resource": "uav-0", "task_id": "task-0",
    }]


def test_delayed_pre_fault_telemetry_is_not_fault_knowledge():
    item = {"event": "disconnect", "event_time": 4.0, "resource": "uav-0", "task_id": "task-0"}
    episode = {"communication_log": [
        {"link": "telemetry", "status": "received", "entity": "uav-0", "field": "connected",
         "measured_at": 3.0, "time": 5.0},
        {"link": "telemetry", "status": "received", "entity": "uav-0", "field": "connected",
         "measured_at": 4.0, "time": 7.0, "message_id": "fault-1"},
    ]}
    assert first_fault_knowledge(episode, item)["message_id"] == "fault-1"


def test_visible_candidate_without_selection_is_attributed_to_policy_choice():
    item = {"tape_id": "t", "event": "disconnect", "event_time": 4.0,
            "resource": "uav-0", "task_id": "task-0"}
    episode = {
        "communication_log": [{"link": "telemetry", "status": "received", "entity": "uav-0",
                                "field": "connected", "measured_at": 4.0, "time": 5.0}],
        "rows": [{"time": 5.0, "before": {"candidate_actions": [{"task_id": "task-0", "uav_id": "uav-1"}]},
                   "action_task": "task-1", "action_uav": "uav-1", "submit": True}],
        "execution_log": [], "commands": [], "tasks": {"task-0": {"state": "expired", "deadline": 8.0}},
        "clock_log": [], "scenario_tasks": [],
    }
    assert classify_pair(item, episode)["category"] == "candidate_visible_but_policy_did_not_select"


def test_no_candidate_after_knowledge_is_not_called_policy_selection_failure():
    item = {"tape_id": "t", "event": "damage", "event_time": 4.0,
            "resource": "uav-0", "task_id": "task-0"}
    episode = {
        "communication_log": [{"link": "telemetry", "status": "received", "entity": "uav-0",
                                "field": "alive", "measured_at": 4.0, "time": 5.0}],
        "rows": [{"time": 5.0, "before": {"candidate_actions": []},
                   "action_task": None, "action_uav": None, "submit": True}],
        "execution_log": [], "commands": {}, "tasks": {"task-0": {"state": "expired", "deadline": 8.0}},
        "clock_log": [], "scenario_tasks": [],
    }
    assert classify_pair(item, episode)["category"] == "known_but_no_public_legal_candidate"


def test_communication_audit_does_not_add_nested_link_statuses():
    result = communication_audit([{"communication_log": [
        {"link": "telemetry", "status": "sent"},
        {"link": "telemetry", "status": "dropped"},
        {"link": "ack", "status": "dropped"},
    ]}])
    assert result["counts"] == {"telemetry:sent": 1, "telemetry:dropped": 1, "ack:dropped": 1}

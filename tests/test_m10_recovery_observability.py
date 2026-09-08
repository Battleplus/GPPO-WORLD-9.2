from pathlib import Path

from gppo_world.m10_communication import CommunicationProfile
from gppo_world.m10_environment import M10Environment, M10Scenario, M10TaskSpec
from tools.audit_m10_recovery_observability import SPLITS, LEVELS, make_candidate, run_public_scheduler
from gppo_world.m10_environment import M10Config


def test_candidate_tapes_are_seeded_and_have_one_interruption():
    a = make_candidate(SPLITS[0], LEVELS[0], 91000)
    b = make_candidate(SPLITS[0], LEVELS[0], 91001)
    assert a.tape_id != b.tape_id
    assert len(a.tasks) == 1
    assert [event.kind for event in a.events].count("damage") + [event.kind for event in a.events].count("disconnect") == 1


def test_reference_eligibility_uses_public_path_and_real_service():
    scenario = make_candidate(SPLITS[0], LEVELS[0], 91000)
    result = run_public_scheduler(scenario, M10Config())
    assert result["interrupted"]
    assert result["fault_knowledge"] is not None
    assert result["first_public_candidate_time"] is not None
    assert result["first_task_accept_time"] is not None
    assert result["post_event_service_count"] > 0
    assert result["completed"]


def test_split_names_are_distinct_for_future_freeze():
    ids = {make_candidate(split, "recovery", 91000 + i).tape_id for i, split in enumerate(SPLITS)}
    assert len(ids) == len(SPLITS)


def test_dropped_telemetry_keeps_addressable_field_identity():
    scenario = M10Scenario(
        "drop-audit", (M10TaskSpec("task-0", 0.0, 0.0, 0.0, 8.0, 1.0, 1.0),),
        (), 71, "test", "drop-audit", CommunicationProfile(name="drop", telemetry_loss_probability=1.0),
    )
    env = M10Environment(M10Config(uav_count=1, task_capacity=1), scenario)
    dropped = [row for row in env._communication_log
               if row.get("link") == "telemetry" and row.get("status") == "dropped"]
    assert dropped
    assert all(row.get("entity") and row.get("field") and isinstance(row.get("sequence"), int)
               for row in dropped)

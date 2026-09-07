"""Causal M-10 task-allocation environment.

This module is deliberately independent from the frozen M-09 GPPO environment.
It connects the M-10 lifecycle, service clock, received-only policy view and
task-level ACK/lease executor into one small, reproducible simulator.  The
policy sees only delivered telemetry snapshots; truth is retained by the
executor and simulator.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
import math
from typing import Any, Iterable

import numpy as np

from .service_clock import ServiceClock, ServiceEvent, ServiceResource
from .task_decision_bridge import TaskDecisionBridge
from .task_execution import TaskCommand, TaskExecution
from .task_lifecycle import TaskLifecycle, TaskState
from .task_policy_view import TaskPolicySnapshot, TaskPolicyView
from .telemetry import Telemetry
from .m10_communication import CommunicationProfile
from .m10_communication import weak_communication_profile


@dataclass(frozen=True)
class M10Config:
    uav_count: int = 4
    task_capacity: int = 6
    region_count: int = 3
    target_count: int = 4
    event_capacity: int = 4
    relation_width: int = 4
    horizon: float = 18.0
    decision_interval: float = 1.0
    ack_latency: float = 0.0
    command_ttl: float = 0.5
    lease_ttl: float = 2.0
    telemetry_max_age: float = 2.5
    telemetry_delay: float = 0.0
    service_rate: float = 1.0
    service_power: float = 1.0
    travel_speed: float = 1.0
    travel_power: float = 0.35
    idle_power: float = 0.05
    initial_energy: float = 9.0
    reward_completion: float = 10.0
    reward_priority_scale: float = 2.0
    penalty_expired: float = 4.0
    penalty_rejected: float = 0.25
    energy_cost_weight: float = 0.08
    seed: int = 0

    def __post_init__(self) -> None:
        if self.uav_count <= 0 or self.task_capacity <= 0 or self.region_count <= 0 or self.target_count <= 0 or self.event_capacity <= 0:
            raise ValueError("positive fleet and task capacity required")
        if not all(math.isfinite(float(v)) for v in self.__dict__.values() if isinstance(v, (int, float))):
            raise ValueError("M10 configuration must be finite")
        if self.horizon <= 0 or self.decision_interval <= 0:
            raise ValueError("positive horizon and decision interval required")
        if self.telemetry_delay < 0:
            raise ValueError("telemetry delay must be nonnegative")
        if self.task_capacity > 32:
            raise ValueError("task capacity is intentionally bounded")

    @property
    def action_count(self) -> int:
        return self.uav_count * self.task_capacity + 1


@dataclass(frozen=True)
class M10TaskSpec:
    task_id: str
    arrival: float
    x: float
    y: float
    deadline: float
    service: float
    priority: float
    region_id: int = 0
    target_id: int = 0


@dataclass(frozen=True)
class M10Scenario:
    name: str
    tasks: tuple[M10TaskSpec, ...]
    events: tuple[ServiceEvent, ...] = ()
    seed: int = 0
    split: str = "regression"
    tape_id: str = "regression-seed-0"
    communication: CommunicationProfile = CommunicationProfile()


def default_scenario(name: str = "mixed", seed: int = 0, *, split: str = "regression") -> M10Scenario:
    """Return a reproducible scenario with all four required perturbation classes.

    The event schedule is public to the simulator but is not injected into the
    policy view.  A separate tape generator can choose which events are sent as
    received telemetry after they occur.
    """
    rng = np.random.default_rng(seed)
    positions = ((1.5, 0.5), (2.5, 2.0), (0.5, 2.5), (3.0, 0.2), (1.0, 3.0), (3.2, 2.8))
    tasks = tuple(
        M10TaskSpec(
            task_id=f"task-{i}",
            arrival=float((0.0, 0.0, 2.0, 3.0, 5.0, 7.0)[i]),
            x=positions[i][0],
            y=positions[i][1],
            deadline=float((7.0, 8.0, 11.0, 12.0, 15.0, 17.0)[i]),
            service=float((1.3, 1.8, 1.0, 2.0, 1.2, 1.6)[i]),
            priority=float((1.0, 1.6, 1.2, 2.0, 1.1, 1.8)[i]),
            region_id=i % 3,
            target_id=i % 4,
        )
        for i in range(6)
    )
    events = (
        ServiceEvent(4.0, "uav-1", "disconnect"),
        ServiceEvent(6.0, "uav-1", "reconnect"),
        ServiceEvent(8.0, "uav-2", "damage"),
    )
    if seed != 0 and split != "regression":
        # Seed-addressed tapes alter both task parameters and the fault tape.
        # The seed-0 regression scenario above remains byte-for-byte stable.
        jittered = []
        for task in tasks:
            arrival = task.arrival if task.arrival == 0 else max(0.0, task.arrival + float(rng.uniform(-0.45, 0.45)))
            deadline = max(arrival + 1.0, task.deadline + float(rng.uniform(-0.65, 0.65)))
            jittered.append(M10TaskSpec(
                task_id=task.task_id,
                arrival=arrival,
                x=max(0.05, task.x + float(rng.normal(0.0, 0.18))),
                y=max(0.05, task.y + float(rng.normal(0.0, 0.18))),
                deadline=deadline,
                service=max(0.35, task.service * float(rng.uniform(0.8, 1.25))),
                priority=max(0.1, task.priority * float(rng.uniform(0.85, 1.15))),
                region_id=int(rng.integers(0, 3)),
                target_id=int(rng.integers(0, 4)),
            ))
        tasks = tuple(jittered)

    if name == "normal":
        events = ()
    elif name == "energy_insufficient":
        tasks = tuple(M10TaskSpec(**{**task.__dict__, "service": task.service * 2.5}) for task in tasks)
    elif name == "uav_damage":
        event_time = 3.0 if seed == 0 else float(rng.uniform(2.0, 5.0))
        events = (ServiceEvent(event_time, f"uav-{0 if seed == 0 else int(rng.integers(0, 4))}", "damage"),)
    elif name == "communication_interrupt":
        uid = "uav-1" if seed == 0 else f"uav-{int(rng.integers(0, 4))}"
        disconnect = 3.0 if seed == 0 else float(rng.uniform(2.0, 5.0))
        events = (ServiceEvent(disconnect, uid, "disconnect"), ServiceEvent(disconnect + 4.0, uid, "reconnect"))
    elif name == "composite":
        pass
    elif name != "mixed":
        raise ValueError(f"unknown M10 scenario: {name}")
    if name == "mixed" and seed != 0 and split != "regression":
        disconnect = float(rng.uniform(2.5, 5.0))
        reconnect = min(10.0, disconnect + float(rng.uniform(2.0, 4.0)))
        link_resource = f"uav-{int(rng.integers(0, 4))}"
        events = (
            ServiceEvent(disconnect, link_resource, "disconnect"),
            ServiceEvent(reconnect, link_resource, "reconnect"),
            ServiceEvent(float(rng.uniform(6.5, 9.5)), f"uav-{int(rng.integers(0, 4))}", "damage"),
        )
    tape_id = f"{split}-{name}-seed-{seed}"
    return M10Scenario(name=name, tasks=tasks, events=events, seed=seed, split=split, tape_id=tape_id)


_TAPE_OFFSETS = {"train": 0, "validation": 1_000_000, "test": 2_000_000, "ood": 3_000_000}


def scenario_tape(split: str, *, count: int, base_seed: int = 7001, name: str = "mixed") -> tuple[M10Scenario, ...]:
    """Freeze a distinct, serializable scenario collection for one split."""
    if split not in _TAPE_OFFSETS:
        raise ValueError(f"unknown tape split: {split}")
    return tuple(default_scenario(name, seed=base_seed + _TAPE_OFFSETS[split] + i, split=split) for i in range(count))


def weak_communication_tape(split: str, *, count: int, base_seed: int = 7001,
                           level: str = "composite", name: str = "mixed") -> tuple[M10Scenario, ...]:
    """Return a distinct, serializable tape with one frozen link protocol."""
    profile = weak_communication_profile(level)
    return tuple(replace(scenario, communication=profile)
                 for scenario in scenario_tape(split, count=count, base_seed=base_seed, name=name))


def scenario_to_dict(scenario: M10Scenario) -> dict[str, Any]:
    return {
        "name": scenario.name,
        "seed": scenario.seed,
        "split": scenario.split,
        "tape_id": scenario.tape_id,
        "tasks": [asdict(task) for task in scenario.tasks],
        "events": [asdict(event) for event in scenario.events],
        "communication": scenario.communication.to_dict(),
    }


def scenario_from_dict(payload: dict[str, Any]) -> M10Scenario:
    return M10Scenario(
        name=str(payload["name"]),
        tasks=tuple(M10TaskSpec(**item) for item in payload["tasks"]),
        events=tuple(ServiceEvent(**item) for item in payload.get("events", [])),
        seed=int(payload.get("seed", 0)), split=str(payload.get("split", "regression")),
        tape_id=str(payload.get("tape_id", "unknown")),
        communication=CommunicationProfile.from_dict(payload.get("communication")),
    )


class M10Environment:
    """Gym-like environment with a fixed global assignment action space."""

    def __init__(self, config: M10Config | None = None, scenario: M10Scenario | None = None):
        self.config = config or M10Config()
        self.scenario = scenario or default_scenario(seed=self.config.seed)
        self.communication = self.scenario.communication
        if len(self.scenario.tasks) > self.config.task_capacity:
            raise ValueError("scenario exceeds public task capacity")
        self.uav_ids = tuple(f"uav-{i}" for i in range(self.config.uav_count))
        self._sequence: dict[tuple[str, str], int] = {}
        self._task_by_id = {task.task_id: task for task in self.scenario.tasks}
        self._last_visible_states: dict[str, str] = {}
        self._event_cursor = 0
        self._reset_state()

    def _reset_state(self) -> None:
        tasks = {
            spec.task_id: TaskLifecycle(
                task_id=spec.task_id,
                arrival=spec.arrival,
                deadline=spec.deadline,
                required_service=spec.service,
                priority=spec.priority,
            )
            for spec in self.scenario.tasks
        }
        resources = {
            uid: ServiceResource(
                energy=self.config.initial_energy,
                service_rate=self.config.service_rate,
                service_power=self.config.service_power,
                position=(0.0, 0.0),
                speed=self.config.travel_speed,
                travel_power=self.config.travel_power,
                idle_power=self.config.idle_power,
            )
            for uid in self.uav_ids
        }
        positions = {spec.task_id: (spec.x, spec.y) for spec in self.scenario.tasks}
        self.clock = ServiceClock(
            tasks,
            resources,
            list(self.scenario.events),
            disconnect_interrupts=True,
            task_positions=positions,
        )
        self.execution = TaskExecution(self.clock, command_ttl=self.config.command_ttl, lease_ttl=self.config.lease_ttl)
        self.view = TaskPolicyView(self.uav_ids, task_capacity=self.config.task_capacity, max_age=self.config.telemetry_max_age)
        self.bridge = TaskDecisionBridge(self.view, self.execution)
        self._sequence = {}
        self._last_visible_states = {}
        self._event_cursor = 0
        self._command_index = 0
        self._step_index = 0
        self._episode_id = f"m10-{self.scenario.name}-{self.config.seed}"
        self._last_energy = sum(resource.energy for resource in self.clock.resources.values())
        self._last_completed = 0
        self._last_expired = 0
        self._feedback_log: list[dict[str, Any]] = []
        self._delivered_messages: list[dict[str, Any]] = []
        self._communication_log: list[dict[str, Any]] = []
        self._pending_messages: list[tuple[str, Telemetry]] = []
        self._public_event_records: list[dict[str, Any]] = []
        self._last_public_event_values: dict[tuple[str, str], float] = {}
        self._public_task_entities: set[str] = set()
        self._trigger_flags: dict[str, bool] = {
            "task_arrival": False,
            "confirmed_fault": False,
            "link_recovery": False,
            "completion_or_invalidation": False,
            "safety_forced": False,
        }
        self._active_command: TaskCommand | None = None
        self._active_action: int | None = None
        self._deliver_observations()
        self._flush_messages()

    def reset(self, *, seed: int | None = None) -> dict[str, Any]:
        if seed is not None and seed != self.config.seed:
            self.config = M10Config(**{**self.config.__dict__, "seed": seed})
            default = default_scenario(self.scenario.name, seed=seed)
            self.scenario = M10Scenario(
                name=default.name, tasks=default.tasks, events=default.events,
                seed=default.seed, split=default.split, tape_id=default.tape_id,
                communication=self.scenario.communication,
            )
            self.communication = self.scenario.communication
        self._reset_state()
        return self._observation(clear_trigger=True)

    def _next_sequence(self, entity: str, field: str) -> int:
        key = (entity, field)
        self._sequence[key] = self._sequence.get(key, 0) + 1
        return self._sequence[key]

    def _send(self, kind: str, entity: str, field: str, value: float) -> None:
        now = self.clock.time
        sequence = self._next_sequence(entity, field)
        identity = f"{kind}|{entity}|{field}|{sequence}|{now:.9f}"
        impairment = self.communication.telemetry(seed=self.scenario.seed, identity=identity, now=now)
        if impairment["dropped"]:
            self._communication_log.append({"link": "telemetry", "status": "dropped", "identity": identity,
                                            "time": now, "reason": "outage" if impairment["outage"] else "random_loss"})
            return
        received_at = now + self.config.telemetry_delay + self.communication.telemetry_extra_delay + impairment["jitter"]
        message = Telemetry(entity, field, float(value), now, received_at, sequence)
        self._communication_log.append({"link": "telemetry", "status": "sent", "identity": identity,
                                        "time": now, "received_at": received_at})
        if message.received_at > now:
            self._pending_messages.append((kind, message))
            if impairment["duplicate"]:
                self._pending_messages.append((kind, message))
            return
        self._accept_message(kind, message, now)

    def _accept_message(self, kind: str, message: Telemetry, now: float) -> bool:
        accepted = self.view.receive(kind, message, now)
        if not accepted:
            self._communication_log.append({"link": "telemetry", "status": "stale_or_duplicate",
                                            "entity": message.entity, "field": message.field,
                                            "sequence": message.sequence, "time": now})
            return False
        self._communication_log.append({"link": "telemetry", "status": "received",
                                        "entity": message.entity, "field": message.field,
                                        "sequence": message.sequence, "time": now,
                                        "measured_at": message.measured_at})
        self._delivered_messages.append({"kind": kind, "entity": message.entity, "field": message.field, "time": now, "measured_at": message.measured_at})
        if kind == "task" and message.entity not in self._public_task_entities:
            self._public_task_entities.add(message.entity)
            self._trigger_flags["task_arrival"] = True
        if kind == "uav" and message.field in ("alive", "connected"):
            key = (message.entity, message.field)
            previous = self._last_public_event_values.get(key)
            current = float(message.value)
            self._last_public_event_values[key] = current
            if previous is not None and previous != current:
                if current < previous:
                    self._trigger_flags["confirmed_fault"] = True
                elif current > previous and message.field == "connected":
                    self._trigger_flags["link_recovery"] = True
                self._public_event_records.append({
                    "entity": message.entity,
                    "field": message.field,
                    "value": current,
                    "measured_at": message.measured_at,
                    "received_at": now,
                })
        if kind == "task" and message.field == "pending":
            key = (message.entity, message.field)
            previous = self._last_public_event_values.get(key)
            current = float(message.value)
            self._last_public_event_values[key] = current
            task = self.clock.tasks.get(message.entity)
            if previous is not None and previous != current and task is not None and task.state in (TaskState.COMPLETED, TaskState.EXPIRED):
                self._trigger_flags["completion_or_invalidation"] = True
        return True

    def _flush_messages(self) -> None:
        now = self.clock.time
        ready = [item for item in self._pending_messages if item[1].received_at <= now]
        self._pending_messages = [item for item in self._pending_messages if item[1].received_at > now]
        for kind, message in sorted(ready, key=lambda item: (item[1].received_at, item[1].entity, item[1].field)):
            if now - message.measured_at > self.config.telemetry_max_age:
                self._communication_log.append({
                    "link": "telemetry", "status": "expired",
                    "entity": message.entity, "field": message.field,
                    "sequence": message.sequence, "time": now,
                    "measured_at": message.measured_at,
                })
                continue
            self._accept_message(kind, message, now)

    def _deliver_observations(self) -> None:
        now = self.clock.time
        for uid, resource in self.clock.resources.items():
            occupied = any(task.assigned_uav == uid for task in self.clock.tasks.values())
            values = {
                "x": resource.position[0], "y": resource.position[1], "energy": resource.energy,
                "alive": float(resource.alive), "connected": float(resource.connected), "idle": float(not occupied),
            }
            for field, value in values.items():
                self._send("uav", uid, field, value)
        for task_id, task in self.clock.tasks.items():
            if task.state == TaskState.UNRELEASED or now < task.arrival:
                continue
            spec = self._task_by_id[task_id]
            values = {
                "x": spec.x, "y": spec.y, "deadline": task.deadline,
                "remaining_service": max(0.0, task.required_service - task.service),
                "priority": task.priority, "pending": float(task.state == TaskState.PENDING),
                "region_id": float(spec.region_id), "target_id": float(spec.target_id),
            }
            for field, value in values.items():
                self._send("task", task_id, field, value)

    def _observation(self, *, clear_trigger: bool = False) -> dict[str, Any]:
        snapshot: TaskPolicySnapshot = self.bridge.observe()
        uavs = np.asarray(snapshot.uavs, dtype=np.float32)
        tasks = np.asarray(snapshot.tasks, dtype=np.float32)
        node_width = 32
        uav_nodes = np.pad(uavs, ((0, 0), (0, node_width - uavs.shape[1])))
        task_nodes = np.asarray(tasks, dtype=np.float32)
        regions = np.zeros((self.config.region_count, node_width), dtype=np.float32)
        targets = np.zeros((self.config.target_count, node_width), dtype=np.float32)
        for index in range(self.config.region_count):
            regions[index, 0] = float(index)
        for index in range(self.config.target_count):
            targets[index, 0] = float(index)
        for row in task_nodes:
            values = row[::4]
            valid = row[2::4]
            if len(values) < 8 or not np.all(valid[:8] > 0.5):
                continue
            region_id = int(round(float(values[6])))
            target_id = int(round(float(values[7])))
            if 0 <= region_id < self.config.region_count:
                regions[region_id, 1] += 1.0
                regions[region_id, 2] += float(values[3])
                regions[region_id, 3] += float(values[4])
                regions[region_id, 4] = float(values[2]) if regions[region_id, 4] == 0 else min(regions[region_id, 4], float(values[2]))
                regions[region_id, 5] = 1.0
            if 0 <= target_id < self.config.target_count:
                targets[target_id, 1] += 1.0
                targets[target_id, 2] += float(values[3])
                targets[target_id, 3] += float(values[4])
                targets[target_id, 4] = float(values[2]) if targets[target_id, 4] == 0 else min(targets[target_id, 4], float(values[2]))
                targets[target_id, 5] = 1.0
        events = np.zeros((self.config.event_capacity, node_width), dtype=np.float32)
        for index, record in enumerate(self._public_event_records[-self.config.event_capacity:]):
            events[index, 0] = 1.0
            events[index, 1] = float(record["field"] == "connected")
            events[index, 2] = float(record["value"])
            events[index, 3] = float(self.uav_ids.index(record["entity"])) / max(1, self.config.uav_count - 1)
            events[index, 4] = max(0.0, self.clock.time - float(record["received_at"]))
            events[index, 5] = float(record["measured_at"]) / self.config.horizon
        relations = np.zeros((self.config.uav_count, self.config.task_capacity, self.config.relation_width), dtype=np.float32)
        for uav_index, uav in enumerate(uavs):
            ux, uy = float(uav[0]), float(uav[4])
            for task_index, task in enumerate(task_nodes):
                tx, ty = float(task[0]), float(task[4])
                visible = float(np.all(task[2::4] > 0.5))
                distance = math.dist((ux, uy), (tx, ty)) / 10.0 if visible else 0.0
                relations[uav_index, task_index] = (distance, visible, float(snapshot.mask[uav_index * self.config.task_capacity + task_index]), float(task[24]) if visible else 0.0)
        # Ordinary telemetry is deliberately not an event trigger.  These
        # flags are raised only by a newly visible semantic change or by a
        # safety gate; the policy never reads the private event schedule.
        trigger_flags = dict(self._trigger_flags)
        event_signal = float(any(trigger_flags.values()))
        flat = np.concatenate((uav_nodes.reshape(-1), regions.reshape(-1), targets.reshape(-1), task_nodes.reshape(-1), events.reshape(-1), relations.reshape(-1), np.asarray([self.clock.time / self.config.horizon, event_signal], dtype=np.float32)))
        result = {
            "flat": flat,
            "uavs": uavs,
            "tasks": tasks,
            "graph": {"node_features": np.concatenate((uav_nodes, regions, targets, task_nodes, events), axis=0), "relations": relations},
            "mask": np.asarray(snapshot.mask, dtype=np.bool_),
            "time": float(self.clock.time),
            "version": int(snapshot.version),
            "types": ("UAV", "Region", "Target", "Task", "Event"),
            "trigger_flags": trigger_flags,
            "event_signal": event_signal,
            # This is an ACKed continuation handle, not a candidate mask.  It
            # lets the controller distinguish a running lease from an unsafe
            # stale allocation candidate without exposing execution truth in
            # the learned feature vector.
            "continuation_action": self._active_action,
        }
        if clear_trigger:
            self._trigger_flags = {key: False for key in self._trigger_flags}
        return result

    def _all_terminal_or_future_empty(self) -> bool:
        return all(task.state in (TaskState.COMPLETED, TaskState.EXPIRED) for task in self.clock.tasks.values()) and self.clock.cursor >= len(self.clock.events)

    def _reward_and_counts(self, feedback: str | TaskCommand) -> tuple[float, dict[str, int]]:
        completed = sum(task.state == TaskState.COMPLETED for task in self.clock.tasks.values())
        expired = sum(task.state == TaskState.EXPIRED for task in self.clock.tasks.values())
        rejected = sum(item.get("result") not in ("accepted", "awaiting_ack", "noop", "reuse_existing") for item in self._feedback_log)
        energy_now = sum(resource.energy for resource in self.clock.resources.values())
        energy_used = max(0.0, self._last_energy - energy_now)
        self._last_energy = energy_now
        reward = -self.config.energy_cost_weight * energy_used
        if feedback not in ("noop", "reuse_existing") and not isinstance(feedback, TaskCommand):
            reward -= self.config.penalty_rejected
        reward += self.config.reward_completion * (completed - self._last_completed)
        reward -= self.config.penalty_expired * (expired - self._last_expired)
        self._last_completed, self._last_expired = completed, expired
        return reward, {"completed": int(completed), "expired": int(expired), "rejected": int(rejected)}

    def step(self, action: int, *, submit_command: bool = True) -> tuple[dict[str, Any], float, bool, dict[str, Any]]:
        if type(action) is not int or not 0 <= action < self.config.action_count:
            raise ValueError("action outside fixed M10 action space")
        obs = self._observation()
        communication_start = len(self._communication_log)
        event_log_before = len(self.clock.log)
        command_id: str | None = None
        lease_renewal = "not_applicable"
        if submit_command:
            self._command_index += 1
            command_id = f"{self._episode_id}-cmd-{self._command_index:05d}"
            command_identity = f"{command_id}|{obs['version']}|{action}"
            command_delivered = self.communication.command_delivered(seed=self.scenario.seed, identity=command_identity)
            self._communication_log.append({"link": "command", "status": "sent" if command_delivered else "dropped",
                                            "command_id": command_id, "time": self.clock.time})
            feedback = (self.bridge.submit(action, version=obs["version"], command_id=command_id)
                        if command_delivered else "command_lost")
            if isinstance(feedback, TaskCommand):
                ack_result = self.execution.acknowledge(feedback.command_id, feedback.uav_id, feedback.token)
                if ack_result == "accepted":
                    self._active_command = feedback
                    self._active_action = action
                    ack_delivered = self.communication.ack_delivered(seed=self.scenario.seed, identity=command_identity)
                    self._communication_log.append({"link": "ack", "status": "received" if ack_delivered else "dropped",
                                                    "command_id": command_id, "time": self.clock.time})
                    if not ack_delivered:
                        feedback = "ack_lost_after_accept"
                else:
                    self._active_command = None
                    self._active_action = None
                    feedback = ack_result
            elif feedback == "noop":
                ack_result = "noop"
                self._active_command = None
                self._active_action = None
            else:
                ack_result = str(feedback)
                self._active_command = None
                self._active_action = None
        else:
            # A non-replanning interval is continuation of the already ACKed
            # lease.  It never creates a new allocation command or bypasses
            # TaskExecution: the executor renews the same fenced lease.
            feedback = "reuse_existing"
            ack_result = "reuse_existing"
            if self._active_command is not None:
                lease_renewal = self.execution.renew(
                    self._active_command.command_id,
                    self._active_command.uav_id,
                    self._active_command.token,
                )
                if lease_renewal != "renewed":
                    self._active_command = None
                    self._active_action = None
        self._feedback_log.append({"command_id": command_id, "result": str(ack_result), "time": self.clock.time})
        target_time = min(self.config.horizon, self.clock.time + self.config.decision_interval)
        self.execution.advance(target_time)
        self._deliver_observations()
        self._flush_messages()
        self._step_index += 1
        next_obs = self._observation(clear_trigger=True)
        if self._active_command is not None and self._active_command.command_id not in self.execution.leases:
            self._active_command = None
            self._active_action = None
        reward, counts = self._reward_and_counts(feedback)
        task_terminal = self._all_terminal_or_future_empty()
        time_limit = self.clock.time >= self.config.horizon
        terminated = bool(task_terminal)
        truncated = bool(time_limit and not terminated)
        info = {
            "feedback": str(ack_result),
            "command_submitted": bool(submit_command),
            "command_id": command_id,
            "lease_renewal": lease_renewal,
            "step": self._step_index,
            "time": self.clock.time,
            "counts": counts,
            "energy": {uid: resource.energy for uid, resource in self.clock.resources.items()},
            "tasks": {task_id: task.state.value for task_id, task in self.clock.tasks.items()},
            "task_service": {task_id: task.service for task_id, task in self.clock.tasks.items()},
            "event_log": list(self.clock.log),
            "new_events": list(self.clock.log[event_log_before:]),
            "feedback_log": list(self._feedback_log),
            "communication_log": list(self._communication_log),
            "communication_delta": list(self._communication_log[communication_start:]),
            "delivered_message_count": len(self._delivered_messages),
            "policy_version": next_obs["version"],
            "trigger_flags": dict(next_obs["trigger_flags"]),
            "terminated": terminated,
            "truncated": truncated,
            "episode_end_reason": "terminated" if terminated else "time_limit" if truncated else None,
        }
        return next_obs, float(reward), bool(terminated or truncated), info

    def action_mask(self) -> np.ndarray:
        return self._observation()["mask"].copy()

    def public_snapshot_digest(self) -> tuple[int, tuple[float, ...], tuple[bool, ...]]:
        obs = self._observation()
        return int(obs["version"]), tuple(float(x) for x in obs["flat"]), tuple(bool(x) for x in obs["mask"])


__all__ = ["M10Config", "M10TaskSpec", "M10Scenario", "M10Environment", "default_scenario", "scenario_tape", "weak_communication_tape", "scenario_to_dict", "scenario_from_dict"]

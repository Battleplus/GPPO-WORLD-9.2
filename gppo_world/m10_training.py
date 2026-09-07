"""Self-contained M-10 PPO, graph/history, world-model and trigger experiments.

The training contract is intentionally small enough to run reproducibly on the
specified server while retaining the real M-10 message/ACK/service semantics.
All policy variants consume the same public observation and action mask; only
the encoder/history/context treatment changes.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import math
import random
import time
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import torch
from torch import nn
from torch.distributions import Categorical

from .m10_environment import M10Config, M10Environment, M10Scenario, default_scenario, scenario_tape, scenario_to_dict


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


@dataclass(frozen=True)
class PPOConfig:
    rollout_steps: int = 256
    update_epochs: int = 4
    learning_rate: float = 3e-4
    gamma: float = 0.99
    gae_lambda: float = 0.95
    clip_epsilon: float = 0.2
    entropy_weight: float = 0.01
    value_weight: float = 0.5
    grad_clip: float = 0.5
    minibatch_size: int = 128


class M10WorldModel(nn.Module):
    """Predict one-step reward/event consequences from public input and action."""

    def __init__(self, obs_dim: int, action_count: int, context_dim: int = 8):
        super().__init__()
        self.obs_dim, self.action_count, self.context_dim = obs_dim, action_count, context_dim
        self.backbone = nn.Sequential(
            nn.Linear(obs_dim + action_count, 128), nn.Tanh(),
            nn.Linear(128, 128), nn.Tanh(),
        )
        self.reward_head = nn.Linear(128, 1)
        self.event_head = nn.Linear(128, 4)
        self.done_head = nn.Linear(128, 1)
        self.context_head = nn.Linear(128, context_dim)

    def forward(self, obs: torch.Tensor, action: torch.Tensor) -> dict[str, torch.Tensor]:
        one_hot = torch.nn.functional.one_hot(action.long(), self.action_count).to(obs.dtype)
        hidden = self.backbone(torch.cat((obs, one_hot), dim=-1))
        return {
            "hidden": hidden,
            "reward": self.reward_head(hidden).squeeze(-1),
            "event_logits": self.event_head(hidden),
            "done_logit": self.done_head(hidden).squeeze(-1),
            "context": self.context_head(hidden),
        }

    @torch.no_grad()
    def context_for(self, obs: torch.Tensor, *, action_mask: torch.Tensor | None = None,
                    action: int | None = None, triggered: bool = False,
                    threshold: float = 0.5, ood_limit: float = 20.0) -> tuple[torch.Tensor, bool, float]:
        """Return an action-conditional expected context over legal candidates.

        A policy decision has no action yet, so the default is an explicit uniform
        expectation over the current legal action mask.  Passing a fixed action is
        allowed only when the caller names it explicitly and proves it legal.
        Non-finite or extreme inputs use the zero-context safety fallback.
        """
        if not torch.isfinite(obs).all() or float(obs.abs().max()) > ood_limit:
            return torch.zeros((obs.shape[0], self.context_dim), device=obs.device, dtype=obs.dtype), False, 1.0
        if action is not None:
            if action_mask is not None and (action < 0 or action >= action_mask.shape[-1] or not bool(action_mask[..., action].all())):
                raise ValueError("reference action is not legal under the supplied mask")
            actions = torch.full((obs.shape[0],), int(action), dtype=torch.long, device=obs.device)
            output = self.forward(obs, actions)
        else:
            if action_mask is None:
                raise ValueError("action_mask is required for action-agnostic world context")
            legal = torch.nonzero(action_mask.bool().flatten(), as_tuple=False).flatten()
            if len(legal) == 0:
                legal = torch.tensor([self.action_count - 1], dtype=torch.long, device=obs.device)
            expanded_obs = obs.repeat(len(legal), 1)
            output = self.forward(expanded_obs, legal.to(obs.device))
        risk = float(torch.sigmoid(output["event_logits"]).max().item())
        context = output["context"].mean(dim=0, keepdim=True) if action is None else output["context"]
        active = not triggered or risk >= threshold
        return context if active else torch.zeros_like(context), active, risk


class M10ActorCritic(nn.Module):
    """PPO actor with explicit entity nodes, relations and candidate scoring."""

    node_width = 32

    def __init__(self, *, uav_count: int, task_capacity: int, action_count: int,
                 encoder: str, type_count: int, history: bool, context_dim: int = 0,
                 region_count: int = 3, target_count: int = 4, event_capacity: int = 4,
                 relation_width: int = 4):
        super().__init__()
        if encoder not in ("mlp", "graph"):
            raise ValueError("encoder must be mlp or graph")
        if type_count not in (2, 5):
            raise ValueError("type_count must be 2 or 5")
        self.uav_count, self.task_capacity, self.action_count = uav_count, task_capacity, action_count
        self.region_count, self.target_count, self.event_capacity = region_count, target_count, event_capacity
        self.relation_width = relation_width
        self.encoder_name, self.type_count, self.history, self.context_dim = encoder, type_count, history, context_dim
        self.node_counts = (uav_count, region_count, target_count, task_capacity, event_capacity)
        self.node_count = sum(self.node_counts)
        self.base_obs_dim = self.node_count * self.node_width + uav_count * task_capacity * relation_width + 2
        self.input_dim = self.base_obs_dim + context_dim
        if encoder == "mlp":
            self.encoder = nn.Sequential(nn.Linear(self.input_dim, 128), nn.Tanh(), nn.Linear(128, 128), nn.Tanh())
            feature_dim = 128
        else:
            self.token_encoder = nn.Sequential(nn.Linear(self.node_width, 64), nn.Tanh(), nn.Linear(64, 64), nn.Tanh())
            self.type_embedding = nn.Embedding(type_count, 64)
            self.graph_projection = nn.Sequential(nn.Linear(64, 128), nn.Tanh())
            self.context_projection = nn.Linear(context_dim, 128) if context_dim else None
            self.edge_encoder = nn.Sequential(nn.Linear(64 * 2 + relation_width, 64), nn.Tanh(), nn.Linear(64, 64), nn.Tanh())
            self.pair_actor = nn.Sequential(nn.Linear(64 + 128, 64), nn.Tanh(), nn.Linear(64, 1))
            self.noop_actor = nn.Linear(128, 1)
            feature_dim = 128
        self.gru = nn.GRU(128, 128, batch_first=True) if history else None
        self.actor = nn.Linear(feature_dim, action_count) if encoder == "mlp" else None
        self.critic = nn.Linear(feature_dim, 1)

    def _unpack(self, obs: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        blocks = []
        start = 0
        for count in self.node_counts:
            size = count * self.node_width
            blocks.append(obs[:, start:start + size].reshape(-1, count, self.node_width))
            start += size
        relations = obs[:, start:start + self.uav_count * self.task_capacity * self.relation_width]
        relations = relations.reshape(-1, self.uav_count, self.task_capacity, self.relation_width)
        return torch.cat(blocks, dim=1), relations, obs[:, -2:]

    def _graph_representation(self, base: torch.Tensor, context: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        tokens, relations, _ = self._unpack(base)
        if self.type_count == 2:
            type_ids = torch.cat((
                torch.zeros(self.uav_count, dtype=torch.long, device=base.device),
                torch.ones(self.node_count - self.uav_count, dtype=torch.long, device=base.device),
            ))
        else:
            type_ids = torch.cat(tuple(torch.full((count,), index, dtype=torch.long, device=base.device)
                                       for index, count in enumerate(self.node_counts)))
        encoded = self.token_encoder(tokens) + self.type_embedding(type_ids)[None, :, :]
        pooled = encoded.mean(dim=1) + encoded.amax(dim=1)
        features = self.graph_projection(pooled)
        if self.context_projection is not None:
            features = features + self.context_projection(context)
        task_start = self.uav_count + self.region_count + self.target_count
        uav_encoded = encoded[:, :self.uav_count]
        task_encoded = encoded[:, task_start:task_start + self.task_capacity]
        pair_input = torch.cat((
            uav_encoded[:, :, None, :].expand(-1, -1, self.task_capacity, -1),
            task_encoded[:, None, :, :].expand(-1, self.uav_count, -1, -1),
            relations,
        ), dim=-1)
        pair_messages = self.edge_encoder(pair_input)
        return features, pair_messages

    def encode(self, obs: torch.Tensor) -> torch.Tensor:
        base = obs[:, :self.base_obs_dim]
        context = obs[:, self.base_obs_dim:]
        if self.encoder_name == "mlp":
            return self.encoder(torch.cat((base, context), dim=-1))
        features, _ = self._graph_representation(base, context)
        return features

    def forward(self, obs: torch.Tensor, hidden: torch.Tensor | None = None):
        base = obs[:, :self.base_obs_dim]
        context = obs[:, self.base_obs_dim:]
        if self.encoder_name == "mlp":
            features = self.encoder(torch.cat((base, context), dim=-1))
            pair_messages = None
        else:
            features, pair_messages = self._graph_representation(base, context)
        next_hidden = hidden
        if self.gru is not None:
            features, next_hidden = self.gru(features[:, None, :], hidden)
            features = features[:, 0, :]
        if pair_messages is None:
            logits = self.actor(features)
        else:
            pair_logits = self.pair_actor(torch.cat((pair_messages, features[:, None, None, :].expand(-1, self.uav_count, self.task_capacity, -1)), dim=-1)).squeeze(-1)
            logits = torch.cat((pair_logits.reshape(-1, self.uav_count * self.task_capacity), self.noop_actor(features)), dim=-1)
        return logits, self.critic(features).squeeze(-1), next_hidden


def masked_distribution(logits: torch.Tensor, mask: torch.Tensor) -> Categorical:
    safe_mask = mask.bool().clone()
    no_action = ~safe_mask.any(dim=-1)
    if no_action.any():
        safe_mask[no_action, -1] = True
    return Categorical(logits=logits.masked_fill(~safe_mask, -1e9))


@dataclass
class Transition:
    obs: np.ndarray
    context: np.ndarray
    mask: np.ndarray
    action: int
    log_prob: float
    value: float
    reward: float
    done: bool
    episode_start: bool
    info: dict[str, Any]


def _public_vector(obs: dict[str, Any], context: np.ndarray | None = None) -> np.ndarray:
    base = np.asarray(obs["flat"], dtype=np.float32)
    extra = np.zeros(0, dtype=np.float32) if context is None else np.asarray(context, dtype=np.float32)
    return np.concatenate((base, extra))


def _make_env(seed: int, scenario_name: str = "mixed", config: M10Config | None = None,
              scenario: M10Scenario | None = None) -> M10Environment:
    cfg = config or M10Config(seed=seed)
    return M10Environment(cfg, scenario or default_scenario(scenario_name, seed=seed, split="train"))


def collect_world_dataset(*, episodes: int, seed: int, config: M10Config,
                          scenarios: Iterable[M10Scenario] | None = None,
                          split: str = "train") -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    tape = list(scenarios or scenario_tape(split, count=episodes, base_seed=seed))
    if len(tape) < episodes:
        raise ValueError("scenario tape is shorter than requested world episodes")
    for episode in range(episodes):
        scenario = tape[episode]
        env = _make_env(scenario.seed, "mixed", config, scenario=scenario)
        obs = env.reset()
        done = False
        while not done:
            before_events = len(env.clock.log)
            rng = np.random.default_rng(seed * 1000 + episode * 17 + int(env.clock.time))
            legal = np.flatnonzero(obs["mask"])
            action = int(rng.choice(legal))
            next_obs, reward, done, info = env.step(action)
            new_events = env.clock.log[before_events:]
            event_target = np.zeros(4, dtype=np.float32)
            names = {"damage": 0, "disconnect": 1, "reconnect": 2}
            for event in new_events:
                event_kind = event.get("kind")
                if event_kind in names:
                    event_target[names[event_kind]] = 1.0
            rows.append({
                "episode": episode,
                "obs": obs["flat"].astype(np.float32),
                "action": action,
                "reward": float(reward),
                "next_obs": next_obs["flat"].astype(np.float32),
                "event_target": event_target,
                "done": float(done),
                "context_target": np.concatenate((np.asarray([float(reward)], dtype=np.float32), event_target, np.asarray([float(done)], dtype=np.float32), next_obs["flat"][-2:].astype(np.float32))),
                "split": split,
                "tape_id": scenario.tape_id,
            })
            obs = next_obs
    return rows


def _world_losses(output: dict[str, torch.Tensor], rewards: torch.Tensor, events: torch.Tensor,
                  dones: torch.Tensor, context_targets: torch.Tensor) -> dict[str, torch.Tensor]:
    return {
        "reward_mse": torch.nn.functional.mse_loss(output["reward"], rewards),
        "event_bce": torch.nn.functional.binary_cross_entropy_with_logits(output["event_logits"], events),
        "done_bce": torch.nn.functional.binary_cross_entropy_with_logits(output["done_logit"], dones),
        "context_mse": torch.nn.functional.mse_loss(output["context"], context_targets),
    }


def _world_metrics(output: dict[str, torch.Tensor], rewards: torch.Tensor, events: torch.Tensor,
                   dones: torch.Tensor, context_targets: torch.Tensor) -> dict[str, float]:
    losses = _world_losses(output, rewards, events, dones, context_targets)
    event_pred = (torch.sigmoid(output["event_logits"]) >= 0.5).to(events.dtype)
    done_pred = (torch.sigmoid(output["done_logit"]) >= 0.5).to(dones.dtype)
    return {
        "reward_rmse": float(losses["reward_mse"].sqrt().detach()),
        "event_bce": float(losses["event_bce"].detach()),
        "event_accuracy": float((event_pred == events).float().mean().detach()),
        "done_bce": float(losses["done_bce"].detach()),
        "done_accuracy": float((done_pred == dones).float().mean().detach()),
        "context_rmse": float(losses["context_mse"].sqrt().detach()),
    }


def train_world_model(rows: list[dict[str, Any]], *, seed: int, action_count: int,
                      epochs: int = 30, device: str = "cpu",
                      ood_rows: list[dict[str, Any]] | None = None) -> tuple[M10WorldModel, dict[str, Any]]:
    if not rows:
        raise ValueError("world-model dataset is empty")
    seed_everything(seed)
    device_obj = torch.device(device)
    obs = torch.tensor(np.stack([row["obs"] for row in rows]), dtype=torch.float32, device=device_obj)
    actions = torch.tensor([row["action"] for row in rows], dtype=torch.long, device=device_obj)
    rewards = torch.tensor([row["reward"] for row in rows], dtype=torch.float32, device=device_obj)
    events = torch.tensor(np.stack([row["event_target"] for row in rows]), dtype=torch.float32, device=device_obj)
    dones = torch.tensor([row["done"] for row in rows], dtype=torch.float32, device=device_obj)
    context_targets = torch.tensor(np.stack([row["context_target"] for row in rows]), dtype=torch.float32, device=device_obj)
    split_values = {str(row.get("split", "")) for row in rows}
    if {"train", "validation", "test"}.issubset(split_values):
        train_idx_list = [i for i, row in enumerate(rows) if row.get("split") == "train"]
        val_idx_list = [i for i, row in enumerate(rows) if row.get("split") == "validation"]
        test_idx_list = [i for i, row in enumerate(rows) if row.get("split") == "test"]
    else:
        episode_ids = sorted({int(row["episode"]) for row in rows})
        rng = np.random.default_rng(seed)
        rng.shuffle(episode_ids)
        n_train_episodes = max(1, int(len(episode_ids) * 0.7))
        n_val_episodes = max(n_train_episodes + 1, int(len(episode_ids) * 0.85))
        train_episodes = set(episode_ids[:n_train_episodes])
        val_episodes = set(episode_ids[n_train_episodes:n_val_episodes])
        test_episodes = set(episode_ids[n_val_episodes:])
        train_idx_list = [i for i, row in enumerate(rows) if row["episode"] in train_episodes]
        val_idx_list = [i for i, row in enumerate(rows) if row["episode"] in val_episodes]
        test_idx_list = [i for i, row in enumerate(rows) if row["episode"] in test_episodes]
    train_idx = torch.tensor(train_idx_list, dtype=torch.long, device=device_obj)
    val_idx = torch.tensor(val_idx_list, dtype=torch.long, device=device_obj)
    test_idx = torch.tensor(test_idx_list, dtype=torch.long, device=device_obj)
    train_episodes = sorted({int(rows[i]["episode"]) for i in train_idx_list})
    val_episodes = sorted({int(rows[i]["episode"]) for i in val_idx_list})
    test_episodes = sorted({int(rows[i]["episode"]) for i in test_idx_list})
    model = M10WorldModel(obs.shape[1], action_count).to(device_obj)
    optimizer = torch.optim.Adam(model.parameters(), lr=3e-4)
    model.optimizer = optimizer  # type: ignore[attr-defined]
    history = []
    for epoch in range(epochs):
        model.train()
        output = model(obs[train_idx], actions[train_idx])
        losses = _world_losses(output, rewards[train_idx], events[train_idx], dones[train_idx], context_targets[train_idx])
        loss = losses["reward_mse"] + losses["event_bce"] + 0.2 * losses["done_bce"] + 0.5 * losses["context_mse"]
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        model.eval()
        with torch.no_grad():
            val_idx_for_loss = val_idx if len(val_idx) else train_idx
            val = model(obs[val_idx_for_loss], actions[val_idx_for_loss])
            val_losses = _world_losses(val, rewards[val_idx_for_loss], events[val_idx_for_loss], dones[val_idx_for_loss], context_targets[val_idx_for_loss])
            val_loss = val_losses["reward_mse"] + val_losses["event_bce"] + 0.2 * val_losses["done_bce"] + 0.5 * val_losses["context_mse"]
        history.append({"epoch": epoch + 1, "train_loss": float(loss.detach()), "validation_loss": float(val_loss.detach()), "context_loss": float(losses["context_mse"].detach())})
    model.eval()
    metadata = {
        "dataset_rows": len(rows), "train_rows": len(train_idx), "validation_rows": len(val_idx), "test_rows": len(test_idx),
        "train_episodes": train_episodes, "validation_episodes": val_episodes, "test_episodes": test_episodes,
        "epochs": epochs, "seed": seed, "history": history, "split_unit": "frozen_episode_tape",
        "loss_weights": {"reward_mse": 1.0, "event_bce": 1.0, "done_bce": 0.2, "context_mse": 0.5},
        "context_target": "[reward,event_0..3,done,time_fraction,event_signal]",
    }
    with torch.no_grad():
        metadata["test_metrics"] = _world_metrics(model(obs[test_idx], actions[test_idx]), rewards[test_idx], events[test_idx], dones[test_idx], context_targets[test_idx])
        train_reward_mean = rewards[train_idx].mean()
        train_event_rate = events[train_idx].mean(dim=0).clamp(1e-5, 1 - 1e-5)
        train_done_rate = dones[train_idx].mean().clamp(1e-5, 1 - 1e-5)
        metadata["test_baseline_metrics"] = {
            "reward_rmse": float(torch.mean((rewards[test_idx] - train_reward_mean) ** 2).sqrt()),
            "event_bce": float(torch.nn.functional.binary_cross_entropy(train_event_rate.expand_as(events[test_idx]), events[test_idx])),
            "done_bce": float(torch.nn.functional.binary_cross_entropy(train_done_rate.expand_as(dones[test_idx]), dones[test_idx])),
        }
        if ood_rows:
            ood_obs = torch.tensor(np.stack([row["obs"] for row in ood_rows]), dtype=torch.float32, device=device_obj)
            ood_actions = torch.tensor([row["action"] for row in ood_rows], dtype=torch.long, device=device_obj)
            ood_rewards = torch.tensor([row["reward"] for row in ood_rows], dtype=torch.float32, device=device_obj)
            ood_events = torch.tensor(np.stack([row["event_target"] for row in ood_rows]), dtype=torch.float32, device=device_obj)
            ood_dones = torch.tensor([row["done"] for row in ood_rows], dtype=torch.float32, device=device_obj)
            ood_context = torch.tensor(np.stack([row["context_target"] for row in ood_rows]), dtype=torch.float32, device=device_obj)
            metadata["ood_metrics"] = _world_metrics(model(ood_obs, ood_actions), ood_rewards, ood_events, ood_dones, ood_context)
    return model, metadata


def _policy_input(env: M10Environment, obs: dict[str, Any], model: M10WorldModel | None,
                  *, fusion: str, device: torch.device, trigger_threshold: float,
                  force_context: bool = False) -> tuple[np.ndarray, bool, float]:
    if model is None or fusion == "base":
        return _public_vector(obs), False, 0.0
    with torch.no_grad():
        context, active, risk = model.context_for(
            torch.tensor(obs["flat"], dtype=torch.float32, device=device)[None, :],
            action_mask=torch.tensor(obs["mask"], dtype=torch.bool, device=device),
            triggered=fusion == "triggered" and not force_context, threshold=trigger_threshold,
        )
    return _public_vector(obs, context[0].detach().cpu().numpy()), active, risk


def _act(policy: M10ActorCritic, vector: np.ndarray, mask: np.ndarray, hidden: torch.Tensor | None,
         device: torch.device, deterministic: bool, forced_action: int | None = None) -> tuple[int, float, float, torch.Tensor | None]:
    obs_tensor = torch.tensor(vector, dtype=torch.float32, device=device)[None, :]
    mask_tensor = torch.tensor(mask, dtype=torch.bool, device=device)[None, :]
    logits, value, hidden = policy(obs_tensor, hidden)
    dist = masked_distribution(logits, mask_tensor)
    action = torch.argmax(dist.logits, dim=-1) if deterministic and forced_action is None else dist.sample()
    if forced_action is not None:
        if not bool(mask_tensor[0, forced_action]):
            forced_action = policy.action_count - 1
        action = torch.tensor([forced_action], dtype=torch.long, device=device)
    return int(action.item()), float(dist.log_prob(action).item()), float(value.item()), hidden


def collect_rollout(policy: M10ActorCritic, *, config: PPOConfig, env_config: M10Config,
                    seed: int, device: torch.device, model: M10WorldModel | None,
                    fusion: str, trigger_threshold: float,
                    scenarios: Iterable[M10Scenario] | None = None,
                    max_replan_interval: int = 3) -> list[Transition]:
    scenario_list = list(scenarios or scenario_tape("train", count=max(8, config.rollout_steps // 8), base_seed=seed))
    env = _make_env(seed, "mixed", env_config, scenario=scenario_list[0])
    obs = env.reset()
    hidden = None
    transitions: list[Transition] = []
    episode_start = True
    scenario_index = 0
    last_action: int | None = None
    steps_since_replan = max_replan_interval
    for _ in range(config.rollout_steps):
        vector, active_context, risk = _policy_input(env, obs, model, fusion=fusion, device=device, trigger_threshold=trigger_threshold)
        event_visible = bool(obs["flat"][-1] > 0.5)
        previous_legal = last_action is not None and bool(obs["mask"][last_action])
        should_replan = fusion != "triggered" or active_context or event_visible or not previous_legal or steps_since_replan >= max_replan_interval
        if should_replan and fusion == "triggered":
            vector, _, risk = _policy_input(env, obs, model, fusion=fusion, device=device, trigger_threshold=trigger_threshold, force_context=True)
        action, log_prob, value, hidden = _act(policy, vector, obs["mask"], hidden, device, deterministic=False, forced_action=None if should_replan else last_action)
        last_action = action
        steps_since_replan = 0 if should_replan else steps_since_replan + 1
        next_obs, reward, done, info = env.step(action)
        info = dict(info)
        info["replan"] = bool(should_replan)
        info["replan_reason"] = "policy_or_forced_event" if should_replan else "reuse_previous_action"
        info["risk"] = float(risk)
        transitions.append(Transition(vector, vector[policy.base_obs_dim:] if policy.context_dim else np.zeros(0, dtype=np.float32), obs["mask"].copy(), action, log_prob, value, reward, done, episode_start, info))
        if done:
            scenario_index = (scenario_index + 1) % len(scenario_list)
            env = _make_env(scenario_list[scenario_index].seed, "mixed", env_config, scenario=scenario_list[scenario_index])
            obs = env.reset()
            hidden = None
            episode_start = True
            last_action = None
            steps_since_replan = max_replan_interval
        else:
            obs = next_obs
            episode_start = False
    return transitions


def _gae(transitions: list[Transition], gamma: float, gae_lambda: float) -> tuple[torch.Tensor, torch.Tensor]:
    rewards = np.asarray([t.reward for t in transitions], dtype=np.float32)
    values = np.asarray([t.value for t in transitions], dtype=np.float32)
    dones = np.asarray([t.done for t in transitions], dtype=np.float32)
    advantages = np.zeros_like(rewards)
    running = 0.0
    for index in range(len(transitions) - 1, -1, -1):
        next_value = 0.0 if index == len(transitions) - 1 else values[index + 1]
        delta = rewards[index] + gamma * next_value * (1.0 - dones[index]) - values[index]
        running = delta + gamma * gae_lambda * (1.0 - dones[index]) * running
        advantages[index] = running
    returns = advantages + values
    advantage_tensor = torch.tensor(advantages, dtype=torch.float32)
    return advantage_tensor, torch.tensor(returns, dtype=torch.float32)


def _evaluate_sequence(policy: M10ActorCritic, transitions: list[Transition], device: torch.device):
    log_probs, values, entropies = [], [], []
    hidden = None
    for transition in transitions:
        if transition.episode_start:
            hidden = None
        obs_tensor = torch.tensor(transition.obs, dtype=torch.float32, device=device)[None, :]
        mask_tensor = torch.tensor(transition.mask, dtype=torch.bool, device=device)[None, :]
        logits, value, hidden = policy(obs_tensor, hidden)
        dist = masked_distribution(logits, mask_tensor)
        action = torch.tensor([transition.action], dtype=torch.long, device=device)
        log_probs.append(dist.log_prob(action)[0])
        entropies.append(dist.entropy()[0])
        values.append(value[0])
    return torch.stack(log_probs), torch.stack(values), torch.stack(entropies)


def update_policy(policy: M10ActorCritic, transitions: list[Transition], *, ppo: PPOConfig,
                  device: torch.device) -> dict[str, float]:
    if not transitions:
        raise ValueError("empty PPO rollout")
    advantages, returns = _gae(transitions, ppo.gamma, ppo.gae_lambda)
    advantages = (advantages - advantages.mean()) / advantages.std(unbiased=False).clamp_min(1e-6)
    old_log_probs = torch.tensor([t.log_prob for t in transitions], dtype=torch.float32, device=device)
    advantages, returns = advantages.to(device), returns.to(device)
    last = {}
    for _ in range(ppo.update_epochs):
        new_log_probs, values, entropy = _evaluate_sequence(policy, transitions, device)
        ratio = (new_log_probs - old_log_probs).exp()
        clipped = torch.clamp(ratio, 1.0 - ppo.clip_epsilon, 1.0 + ppo.clip_epsilon)
        policy_loss = -torch.min(ratio * advantages, clipped * advantages).mean()
        value_loss = torch.nn.functional.mse_loss(values, returns)
        entropy_mean = entropy.mean()
        loss = policy_loss + ppo.value_weight * value_loss - ppo.entropy_weight * entropy_mean
        policy.optimizer.zero_grad(set_to_none=True)  # type: ignore[attr-defined]
        loss.backward()
        torch.nn.utils.clip_grad_norm_(policy.parameters(), ppo.grad_clip)
        policy.optimizer.step()  # type: ignore[attr-defined]
        last = {"loss": float(loss.detach()), "policy_loss": float(policy_loss.detach()), "value_loss": float(value_loss.detach()), "entropy": float(entropy_mean.detach()), "approx_kl": float((old_log_probs - new_log_probs).mean().detach())}
    return last


def train_policy(*, variant: str, encoder: str, type_count: int, history: bool,
                  fusion: str, model: M10WorldModel | None, seed: int, steps: int,
                  env_config: M10Config, ppo_config: PPOConfig, device: str,
                  trigger_threshold: float = 0.5,
                  scenarios: Iterable[M10Scenario] | None = None,
                  max_replan_interval: int = 3) -> tuple[M10ActorCritic, dict[str, Any]]:
    if fusion not in ("base", "world", "triggered"):
        raise ValueError("unsupported fusion")
    seed_everything(seed)
    device_obj = torch.device(device)
    context_dim = model.context_dim if model is not None and fusion != "base" else 0
    policy = M10ActorCritic(
        uav_count=env_config.uav_count, task_capacity=env_config.task_capacity,
        action_count=env_config.action_count, encoder=encoder, type_count=type_count,
        history=history, context_dim=context_dim,
        region_count=env_config.region_count, target_count=env_config.target_count,
        event_capacity=env_config.event_capacity, relation_width=env_config.relation_width,
    ).to(device_obj)
    policy.optimizer = torch.optim.Adam(policy.parameters(), lr=ppo_config.learning_rate)  # type: ignore[attr-defined]
    effective = PPOConfig(**{**asdict(ppo_config), "rollout_steps": min(ppo_config.rollout_steps, steps)})
    updates = []
    total_steps = 0
    started = time.perf_counter()
    while total_steps < steps:
        effective = PPOConfig(**{**asdict(effective), "rollout_steps": min(effective.rollout_steps, steps - total_steps)})
        transitions = collect_rollout(policy, config=effective, env_config=env_config, seed=seed + total_steps, device=device_obj, model=model, fusion=fusion, trigger_threshold=trigger_threshold, scenarios=scenarios, max_replan_interval=max_replan_interval)
        updates.append(update_policy(policy, transitions, ppo=effective, device=device_obj))
        total_steps += len(transitions)
    elapsed = time.perf_counter() - started
    metadata = {
        "variant": variant, "encoder": encoder, "type_count": type_count, "history": history,
        "fusion": fusion, "seed": seed, "steps": total_steps, "optimizer_updates": len(updates),
        "elapsed_seconds": elapsed, "steps_per_second": total_steps / max(elapsed, 1e-9),
        "updates": updates, "device": str(device_obj), "env_config": asdict(env_config), "ppo_config": asdict(ppo_config),
        "trigger_threshold": trigger_threshold, "max_replan_interval": max_replan_interval,
        "replans": int(sum(bool(t.info.get("replan")) for t in transitions)) if transitions else 0,
    }
    return policy, metadata


def evaluate_policy(policy: M10ActorCritic, *, model: M10WorldModel | None, fusion: str,
                    env_config: M10Config, seeds: Iterable[int], device: str,
                    trigger_threshold: float = 0.5,
                    scenarios: dict[int, M10Scenario] | None = None,
                    max_replan_interval: int = 3) -> dict[str, Any]:
    device_obj = torch.device(device)
    policy.eval()
    records = []
    for seed in seeds:
        scenario = scenarios.get(seed) if scenarios else None
        env = _make_env(seed, "mixed", env_config, scenario=scenario)
        obs = env.reset()
        hidden = None
        done = False
        total_reward = 0.0
        steps = 0
        trigger_count = 0
        replan_reasons: dict[str, int] = {}
        last_action: int | None = None
        steps_since_replan = max_replan_interval
        while not done and steps < int(env_config.horizon / env_config.decision_interval) + 2:
            vector, active, risk = _policy_input(env, obs, model, fusion=fusion, device=device_obj, trigger_threshold=trigger_threshold)
            event_visible = bool(obs["flat"][-1] > 0.5)
            previous_legal = last_action is not None and bool(obs["mask"][last_action])
            should_replan = fusion != "triggered" or active or event_visible or not previous_legal or steps_since_replan >= max_replan_interval
            if should_replan and fusion == "triggered":
                vector, _, risk = _policy_input(env, obs, model, fusion=fusion, device=device_obj, trigger_threshold=trigger_threshold, force_context=True)
            action, _, _, hidden = _act(policy, vector, obs["mask"], hidden, device_obj, deterministic=True, forced_action=None if should_replan else last_action)
            last_action = action
            steps_since_replan = 0 if should_replan else steps_since_replan + 1
            if should_replan and fusion == "triggered":
                trigger_count += 1
                reason = "public_event" if event_visible else "risk_or_max_wait" if active or steps_since_replan == 0 else "safety_or_initial"
                replan_reasons[reason] = replan_reasons.get(reason, 0) + 1
            obs, reward, done, info = env.step(action)
            total_reward += reward
            steps += 1
        counts = info["counts"]
        records.append({"seed": seed, "return": total_reward, "steps": steps, "completed": counts["completed"], "expired": counts["expired"], "rejected": counts["rejected"], "trigger_count": trigger_count, "replan_reasons": replan_reasons, "energy_remaining": float(sum(info["energy"].values())), "task_states": info["tasks"]})
    keys = ("return", "completed", "expired", "rejected", "energy_remaining")
    summary = {key: {"mean": float(np.mean([row[key] for row in records])), "std": float(np.std([row[key] for row in records]))} for key in keys}
    return {"episodes": records, "summary": summary, "fusion": fusion}


@torch.no_grad()
def calibrate_trigger_threshold(model: M10WorldModel, rows: list[dict[str, Any]], *, device: str) -> dict[str, Any]:
    """Select a trigger threshold using validation rows only."""
    if not rows:
        raise ValueError("validation rows are required for trigger calibration")
    device_obj = torch.device(device)
    obs = torch.tensor(np.stack([row["obs"] for row in rows]), dtype=torch.float32, device=device_obj)
    mask = torch.full((len(rows), model.action_count), True, dtype=torch.bool, device=device_obj)
    actions = torch.tensor([row["action"] for row in rows], dtype=torch.long, device=device_obj)
    outputs = model(obs, actions)
    risks = torch.sigmoid(outputs["event_logits"]).max(dim=-1).values.cpu().numpy()
    targets = np.asarray([float(np.max(row["event_target"])) for row in rows], dtype=np.float32)
    candidates = [round(x, 2) for x in np.arange(0.1, 0.91, 0.05)]
    scores = []
    for threshold in candidates:
        pred = risks >= threshold
        tp = float(np.sum(pred & (targets > 0.5)))
        fp = float(np.sum(pred & (targets <= 0.5)))
        fn = float(np.sum((~pred) & (targets > 0.5)))
        precision = tp / max(tp + fp, 1.0)
        recall = tp / max(tp + fn, 1.0)
        f1 = 2 * precision * recall / max(precision + recall, 1e-9)
        scores.append({"threshold": threshold, "f1": f1, "precision": precision, "recall": recall})
    best = max(scores, key=lambda item: (item["f1"], -item["threshold"]))
    return {"selected_threshold": best["threshold"], "selection_unit": "validation_rows_only", "candidates": scores, "validation_rows": len(rows)}


def save_policy(path: Path, policy: M10ActorCritic, metadata: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"state_dict": policy.state_dict(), "metadata": metadata,
               "optimizer_state_dict": policy.optimizer.state_dict() if hasattr(policy, "optimizer") else None,
               "recovery_state": {"steps": int(metadata.get("steps", 0)), "seed": metadata.get("seed"), "variant": metadata.get("variant")}}
    torch.save(payload, path)


__all__ = [
    "M10WorldModel", "M10ActorCritic", "M10Config", "PPOConfig",
    "collect_world_dataset", "train_world_model", "calibrate_trigger_threshold", "train_policy", "evaluate_policy", "save_policy",
]

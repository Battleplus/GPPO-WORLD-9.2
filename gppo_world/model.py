"""Action-conditioned heterogeneous-graph temporal world model."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Mapping

import torch
from torch import nn

from .contracts import GraphSnapshot, Relation
from .data import COST_NAMES, STATE_DIM, state_vector
from .registry import FEATURE_REGISTRY, SCHEMA_VERSION


RELATIONS = tuple(FEATURE_REGISTRY.edges)
def _relation_key(relation: Relation) -> str:
    return "__".join(relation)


@dataclass(frozen=True)
class WorldModelConfig:
    hidden_dim: int = 64
    graph_dim: int = 64
    action_dim: int = 24
    stochastic_dim: int = 24
    message_layers: int = 1
    num_actions_with_reject: int = 18


class HeteroGraphEncoder(nn.Module):
    def __init__(self, config: WorldModelConfig):
        super().__init__()
        h = config.hidden_dim
        self.encoders = nn.ModuleDict(
            {
                name: nn.Sequential(nn.Linear(dim, h), nn.LayerNorm(h), nn.SiLU())
                for name, dim in FEATURE_REGISTRY.node_dimensions.items()
            }
        )
        self.messages = nn.ModuleList(
            [
                nn.ModuleDict(
                    {
                        _relation_key(relation): nn.Sequential(
                            nn.Linear(h + FEATURE_REGISTRY.edge_dimensions[relation], h), nn.SiLU()
                        )
                        for relation in RELATIONS
                    }
                )
                for _ in range(config.message_layers)
            ]
        )
        self.updates = nn.ModuleList(
            [
                nn.ModuleDict(
                    {
                        name: nn.Sequential(nn.Linear(2 * h, h), nn.LayerNorm(h), nn.SiLU())
                        for name in FEATURE_REGISTRY.nodes
                    }
                )
                for _ in range(config.message_layers)
            ]
        )
        self.pool = nn.Sequential(nn.Linear(3 * h, config.graph_dim), nn.LayerNorm(config.graph_dim), nn.SiLU())

    def forward(self, graph: GraphSnapshot) -> torch.Tensor:
        hidden = {name: self.encoders[name](value) for name, value in graph.nodes.items()}
        for layer_messages, layer_updates in zip(self.messages, self.updates):
            totals = {name: torch.zeros_like(value) for name, value in hidden.items()}
            counts = {
                name: torch.zeros((value.shape[0], 1), device=value.device, dtype=value.dtype)
                for name, value in hidden.items()
            }
            for relation in RELATIONS:
                src_type, _, dst_type = relation
                index = graph.edge_index[relation]
                src, dst = index[0], index[1]
                message_input = torch.cat([hidden[src_type][src], graph.edge_attr[relation]], dim=-1)
                message = layer_messages[_relation_key(relation)](message_input)
                totals[dst_type].index_add_(0, dst, message)
                counts[dst_type].index_add_(
                    0, dst, torch.ones((dst.shape[0], 1), device=message.device, dtype=message.dtype)
                )
            hidden = {
                name: layer_updates[name](
                    torch.cat([value, totals[name] / counts[name].clamp_min(1.0)], dim=-1)
                )
                for name, value in hidden.items()
            }
        pooled = torch.cat([hidden[name].mean(dim=0) for name in ("uav", "region", "target")], dim=-1)
        return self.pool(pooled)


class PredictionHeads(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int):
        super().__init__()
        self.trunk = nn.Sequential(nn.Linear(input_dim, hidden_dim), nn.SiLU())
        self.state_mean = nn.Linear(hidden_dim, STATE_DIM)
        self.state_change_logit = nn.Linear(hidden_dim, STATE_DIM)
        self.state_logvar = nn.Linear(hidden_dim, STATE_DIM)
        self.reward_mean = nn.Linear(hidden_dim, 1)
        self.reward_logvar = nn.Linear(hidden_dim, 1)
        self.cost_mean = nn.Linear(hidden_dim, len(COST_NAMES))
        self.cost_logvar = nn.Linear(hidden_dim, len(COST_NAMES))
        self.continuation_logit = nn.Linear(hidden_dim, 1)

    def forward(self, value: torch.Tensor) -> dict[str, torch.Tensor]:
        hidden = self.trunk(value)
        raw_delta = torch.tanh(self.state_mean(hidden))
        change_probability = torch.sigmoid(self.state_change_logit(hidden))
        soft_delta = raw_delta * change_probability
        return {
            "state_delta_soft": soft_delta,
            "state_delta_raw": raw_delta,
            "state_change_logit": self.state_change_logit(hidden),
            "state_change_probability": change_probability,
            "state_logvar": self.state_logvar(hidden).clamp(-6.0, 3.0),
            "reward": self.reward_mean(hidden).squeeze(-1),
            "reward_logvar": self.reward_logvar(hidden).squeeze(-1).clamp(-6.0, 3.0),
            "costs": self.cost_mean(hidden),
            "cost_logvar": self.cost_logvar(hidden).clamp(-6.0, 3.0),
            "continuation_logit": self.continuation_logit(hidden).squeeze(-1),
        }


class GraphWorldModel(nn.Module):
    """Graph encoder + action-conditioned GRU + stochastic latent heads."""

    format_version = "gppo-graph-world-model-v1"

    def __init__(self, config: WorldModelConfig | None = None):
        super().__init__()
        self.config = config or WorldModelConfig()
        c = self.config
        self.graph_encoder = HeteroGraphEncoder(c)
        self.action_encoder = nn.Embedding(c.num_actions_with_reject, c.action_dim)
        self.action_context_encoder = nn.Sequential(
            nn.Linear(12 + 12 + FEATURE_REGISTRY.edge_dimensions[("uav", "can_serve", "region")], c.action_dim),
            nn.LayerNorm(c.action_dim),
            nn.SiLU(),
        )
        self.gru = nn.GRUCell(c.graph_dim + c.action_dim, c.hidden_dim)
        self.posterior = nn.Linear(c.hidden_dim + c.graph_dim, 2 * c.stochastic_dim)
        self.heads = PredictionHeads(c.hidden_dim + c.stochastic_dim + c.action_dim, c.hidden_dim)
        self.register_buffer("change_threshold", torch.tensor(0.5, dtype=torch.float32))

    def initial_state(self, device: torch.device | str = "cpu") -> torch.Tensor:
        return torch.zeros(self.config.hidden_dim, device=device)

    def _action_embedding(self, graph: GraphSnapshot, action: int | None) -> torch.Tensor:
        device = graph.nodes["uav"].device
        if action is None:
            return torch.zeros(self.config.action_dim, device=device)
        action_tensor = torch.tensor(int(action), device=device, dtype=torch.long)
        embedding = self.action_encoder(action_tensor)
        if 0 <= int(action) < int(graph.candidate_edges.shape[0]):
            uav_index, region_index = graph.candidate_edges[int(action)].tolist()
            context = torch.cat(
                [
                    graph.nodes["uav"][uav_index],
                    graph.nodes["region"][region_index],
                    graph.edge_attr[("uav", "can_serve", "region")][int(action)],
                ]
            )
            embedding = embedding + self.action_context_encoder(context)
        return embedding

    def step(
        self,
        graph: GraphSnapshot,
        action: int | None,
        hidden: torch.Tensor | None = None,
        *,
        sample: bool | None = None,
    ) -> tuple[dict[str, torch.Tensor], torch.Tensor]:
        graph_embedding = self.graph_encoder(graph)
        action_embedding = self._action_embedding(graph, action)
        if hidden is None:
            hidden = self.initial_state(graph_embedding.device)
        next_hidden = self.gru(torch.cat([graph_embedding, action_embedding]), hidden)
        mean, logvar = self.posterior(torch.cat([next_hidden, graph_embedding])).chunk(2, dim=-1)
        logvar = logvar.clamp(-8.0, 4.0)
        should_sample = self.training if sample is None else sample
        stochastic = mean + torch.randn_like(mean) * torch.exp(0.5 * logvar) if should_sample else mean
        outputs = self.heads(torch.cat([next_hidden, stochastic, action_embedding]))
        hard_gate = (outputs["state_change_probability"] >= self.change_threshold).to(outputs["state_delta_raw"].dtype)
        outputs["state_delta"] = (
            outputs["state_delta_soft"] if self.training else outputs["state_delta_raw"] * hard_gate
        )
        outputs.update({"h": next_hidden, "z": stochastic, "z_mean": mean, "z_logvar": logvar})
        return outputs, next_hidden

    def save(self, path: str | Path, *, extra: Mapping | None = None) -> None:
        payload = {
            "format": self.format_version,
            "config": asdict(self.config),
            "schema_version": SCHEMA_VERSION,
            "registry_sha256": FEATURE_REGISTRY.sha256(),
            "state_dict": self.state_dict(),
            "extra": dict(extra or {}),
        }
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        torch.save(payload, Path(path))

    @classmethod
    def load(cls, path: str | Path, *, map_location: str | torch.device = "cpu"):
        payload = torch.load(Path(path), map_location=map_location, weights_only=False)
        if payload.get("format") != cls.format_version:
            raise ValueError("unsupported world-model checkpoint format")
        if payload.get("schema_version") != SCHEMA_VERSION:
            raise ValueError("world-model schema mismatch")
        if payload.get("registry_sha256") != FEATURE_REGISTRY.sha256():
            raise ValueError("feature registry mismatch")
        model = cls(WorldModelConfig(**payload["config"]))
        model.load_state_dict(payload["state_dict"])
        return model, dict(payload.get("extra", {}))


class FlatGRUWorldModel(nn.Module):
    """Equal-output summary-vector GRU baseline without graph relations."""

    def __init__(self, config: WorldModelConfig | None = None):
        super().__init__()
        self.config = config or WorldModelConfig()
        c = self.config
        self.state_encoder = nn.Sequential(
            nn.Linear(STATE_DIM, c.graph_dim), nn.LayerNorm(c.graph_dim), nn.SiLU()
        )
        self.action_encoder = nn.Embedding(c.num_actions_with_reject, c.action_dim)
        self.gru = nn.GRUCell(c.graph_dim + c.action_dim, c.hidden_dim)
        self.heads = PredictionHeads(c.hidden_dim + c.action_dim, c.hidden_dim)
        self.register_buffer("change_threshold", torch.tensor(0.5, dtype=torch.float32))

    def initial_state(self, device: torch.device | str = "cpu") -> torch.Tensor:
        return torch.zeros(self.config.hidden_dim, device=device)

    def step(self, graph: GraphSnapshot, action: int | None, hidden=None, *, sample=None):
        encoded = self.state_encoder(state_vector(graph))
        if action is None:
            action_embedding = torch.zeros(self.config.action_dim, device=encoded.device)
        else:
            action_tensor = torch.tensor(int(action), device=encoded.device, dtype=torch.long)
            action_embedding = self.action_encoder(action_tensor)
        if hidden is None:
            hidden = self.initial_state(encoded.device)
        next_hidden = self.gru(torch.cat([encoded, action_embedding]), hidden)
        outputs = self.heads(torch.cat([next_hidden, action_embedding]))
        hard_gate = (outputs["state_change_probability"] >= self.change_threshold).to(outputs["state_delta_raw"].dtype)
        outputs["state_delta"] = (
            outputs["state_delta_soft"] if self.training else outputs["state_delta_raw"] * hard_gate
        )
        zero = torch.zeros(1, device=encoded.device)
        outputs.update({"h": next_hidden, "z": zero, "z_mean": zero, "z_logvar": zero})
        return outputs, next_hidden

    def save(self, path: str | Path, *, extra: Mapping | None = None) -> None:
        payload = {
            "format": "gppo-flat-gru-world-model-v1",
            "config": asdict(self.config),
            "schema_version": SCHEMA_VERSION,
            "registry_sha256": FEATURE_REGISTRY.sha256(),
            "state_dict": self.state_dict(),
            "extra": dict(extra or {}),
        }
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        torch.save(payload, Path(path))

    @classmethod
    def load(cls, path: str | Path, *, map_location: str | torch.device = "cpu"):
        payload = torch.load(Path(path), map_location=map_location, weights_only=False)
        if payload.get("format") != "gppo-flat-gru-world-model-v1":
            raise ValueError("unsupported flat-GRU checkpoint format")
        if payload.get("schema_version") != SCHEMA_VERSION:
            raise ValueError("flat-GRU schema mismatch")
        if payload.get("registry_sha256") != FEATURE_REGISTRY.sha256():
            raise ValueError("flat-GRU feature registry mismatch")
        model = cls(WorldModelConfig(**payload["config"]))
        model.load_state_dict(payload["state_dict"])
        return model, dict(payload.get("extra", {}))

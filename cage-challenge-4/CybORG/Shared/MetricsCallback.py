from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any


@dataclass
class MetricsCallback:
    """Lightweight callback used by custom submissions during evaluation.

    The evaluation wrappers call `on_reset()` once per episode and `on_step()`
    each environment step. This implementation is intentionally minimal and
    dependency-free so submissions can run even when optional logging stacks
    (e.g. wandb/ray callbacks) are not configured.
    """

    episode: int = 0
    step: int = 0
    cumulative_reward: float = 0.0
    last_actions: dict[str, Any] = field(default_factory=dict)
    trace_path: str | None = None

    def __post_init__(self) -> None:
        self.trace_path = os.environ.get("CAGE4_METRICS_TRACE_PATH")

    def _append_trace(self, payload: dict[str, Any]) -> None:
        if not self.trace_path:
            return
        try:
            with open(self.trace_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(payload, ensure_ascii=False) + "\n")
        except Exception:
            # Keep callback fail-safe during evaluation.
            pass

    def on_reset(self, env: Any) -> None:
        self.episode += 1
        self.step = 0
        self.cumulative_reward = 0.0
        self.last_actions.clear()
        self._append_trace({"event": "episode_start", "episode": self.episode})

    def on_step(
        self,
        observations: dict[str, Any] | None,
        actions: dict[str, Any] | None,
        rewards: dict[str, float] | None,
        env: Any,
    ) -> None:
        self.step += 1
        if actions:
            self.last_actions = dict(actions)

        reward_total = float(sum((rewards or {}).values()))
        self.cumulative_reward += reward_total

        self._append_trace(
            {
                "event": "step",
                "episode": self.episode,
                "step": self.step,
                "reward_step_total": reward_total,
                "reward_cumulative": self.cumulative_reward,
                "actions": {k: getattr(v, "__class__", type(v)).__name__ for k, v in (actions or {}).items()},
            }
        )

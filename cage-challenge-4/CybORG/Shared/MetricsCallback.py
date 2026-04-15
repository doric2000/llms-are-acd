from __future__ import annotations

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
    last_actions: dict[str, Any] = field(default_factory=dict)

    def on_reset(self, env: Any) -> None:
        self.episode += 1
        self.step = 0
        self.last_actions.clear()

    def on_step(
        self,
        observations: dict[str, Any] | None,
        actions: dict[str, Any] | None,
        env: Any,
    ) -> None:
        self.step += 1
        if actions:
            self.last_actions = dict(actions)

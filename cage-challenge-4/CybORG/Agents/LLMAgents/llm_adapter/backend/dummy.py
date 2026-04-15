from __future__ import annotations

from typing import Dict, List

from CybORG.Agents.LLMAgents.llm_adapter.backend.model_backend import ModelBackend


class DummyBackend(ModelBackend):
	"""Backend used for offline tests and safe fallbacks."""

	def generate(self, messages: List[Dict[str, str]]) -> str:
		return '{"action": "Sleep", "reason": "Dummy backend fallback"}'

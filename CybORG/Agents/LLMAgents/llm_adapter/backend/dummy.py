from __future__ import annotations

from typing import List, Dict

from CybORG.Agents.LLMAgents.llm_adapter.backend.model_backend import ModelBackend

class DummyBackend(ModelBackend):
    """Dummy model backend for testing."""

    def generate(self, messages: List[Dict[str, str]]) -> str:
        return '{"action": "Sleep", "reason": "Dummy backend fallback"}'
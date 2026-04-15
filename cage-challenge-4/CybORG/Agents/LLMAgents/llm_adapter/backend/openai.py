from __future__ import annotations

import os
from typing import Dict, List

from openai import OpenAI

from CybORG.Agents.LLMAgents.llm_adapter.backend.model_backend import ModelBackend


class OpenAIBackend(ModelBackend):
	"""OpenAI-compatible backend for chat completion models."""

	def __init__(self, hyperparams: dict, api_key: str | None):
		self.base_url = hyperparams.get("base_url") or os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
		self.model_name = hyperparams["model_name"]
		self.temperature = hyperparams["generate"]["temperature"]
		self.max_tokens = hyperparams["generate"]["max_new_tokens"]
		self.extra_headers = hyperparams.get("extra_headers", {})
		self.openai_client = OpenAI(base_url=self.base_url, api_key=api_key or os.environ.get("OPENAI_API_KEY", "dummy"))

	def generate(self, messages: List[Dict[str, str]]) -> str:
		completion = self.openai_client.chat.completions.create(
			model=self.model_name,
			messages=messages,
			max_tokens=self.max_tokens,
			temperature=self.temperature,
			extra_headers=self.extra_headers or None,
		)
		message = completion.choices[0].message
		content = message.content or getattr(message, "reasoning", "") or ""
		return content.strip()


class NewOpenAIBackend(OpenAIBackend):
	"""Alias for newer OpenAI-compatible endpoints."""

	def __init__(self, hyperparams: dict, api_key: str | None):
		hyperparams = dict(hyperparams)
		hyperparams.setdefault("base_url", os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"))
		super().__init__(hyperparams=hyperparams, api_key=api_key)

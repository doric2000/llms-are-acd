from __future__ import annotations

from typing import Dict, List

from CybORG.Agents.LLMAgents.llm_adapter.backend.model_backend import ModelBackend


class HuggingFaceBackend(ModelBackend):
	"""Minimal Hugging Face backend backed by a text-generation pipeline."""

	def __init__(self, hyperparams: dict, token: str | None):
		self.hyperparams = hyperparams
		self.token = token
		self.model_name = hyperparams["model_name"]
		self.temperature = hyperparams["generate"]["temperature"]
		self.max_tokens = hyperparams["generate"]["max_new_tokens"]
		self._pipeline = None

	def _load_pipeline(self):
		if self._pipeline is not None:
			return self._pipeline

		try:
			from transformers import pipeline
		except ImportError as exc:
			raise ImportError("transformers is required for HuggingFaceBackend") from exc

		self._pipeline = pipeline(
			"text-generation",
			model=self.model_name,
			token=self.token,
		)
		return self._pipeline

	def generate(self, messages: List[Dict[str, str]]) -> str:
		prompt = self._format_messages_history(messages)
		generator = self._load_pipeline()
		outputs = generator(
			prompt,
			max_new_tokens=self.max_tokens,
			temperature=self.temperature,
			do_sample=self.temperature > 0,
		)
		if not outputs:
			return ""
		generated_text = outputs[0].get("generated_text", "")
		return self._format_response(generated_text)

import os
from typing import Dict, List

from openai import OpenAI

from CybORG.Agents.LLMAgents.llm_adapter.backend.model_backend import ModelBackend


class OllamaBackend(ModelBackend):
    """Ollama model backend using the OpenAI-compatible API."""

    def __init__(self, hyperparams: dict):
        base_url = os.environ.get("OLLAMA_BASE_URL", hyperparams.get("base_url", "http://127.0.0.1:11434/v1"))
        self.model_name = hyperparams["model_name"]
        self.temperature = hyperparams["generate"]["temperature"]
        self.max_tokens = hyperparams["generate"]["max_new_tokens"]
        self.ollama_options = dict(hyperparams.get("ollama_options", {}))
        self.keep_alive = hyperparams.get("keep_alive")
        self.request_timeout_sec = float(hyperparams.get("request_timeout_sec", 20))
        self.max_retries = int(hyperparams.get("max_retries", 0))
        self.openai_client = OpenAI(
            base_url=base_url,
            api_key="ollama",
            timeout=self.request_timeout_sec,
            max_retries=self.max_retries,
        )

    def generate(self, messages: List[Dict[str, str]]) -> str:
        extra_body = {}
        if self.ollama_options:
            extra_body["options"] = self.ollama_options
        if self.keep_alive is not None:
            extra_body["keep_alive"] = self.keep_alive

        completion = self.openai_client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            extra_body=extra_body or None,
        )

        message = completion.choices[0].message
        content = message.content or ""

        # DeepSeek-R1 on Ollama can emit only `reasoning` when token budget is tight.
        # Fall back to that field to avoid empty assistant responses.
        if not content:
            content = getattr(message, "reasoning", "") or ""

        return content.strip()
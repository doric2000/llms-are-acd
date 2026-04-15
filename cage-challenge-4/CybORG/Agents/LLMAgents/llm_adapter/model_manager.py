from __future__ import annotations

import ast
import copy
import json
import os
import re
from typing import Any, Dict, List, Mapping

from CybORG.Agents.LLMAgents.llm_adapter.backend.model_backend import ModelBackend


HF_TOKEN = os.environ.get("HF_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")


class BackendFactory:
	"""Factory class for creating model backend instances."""

	@staticmethod
	def create_backend(backend_name: str, hyperparams: dict) -> ModelBackend:
		backend_name = backend_name.lower()
		if backend_name == "openai":
			from CybORG.Agents.LLMAgents.llm_adapter.backend.openai import OpenAIBackend

			return OpenAIBackend(hyperparams=hyperparams, api_key=OPENAI_API_KEY)
		if backend_name == "new-openai":
			from CybORG.Agents.LLMAgents.llm_adapter.backend.openai import NewOpenAIBackend

			return NewOpenAIBackend(hyperparams=hyperparams, api_key=OPENAI_API_KEY)
		if backend_name == "huggingface":
			from CybORG.Agents.LLMAgents.llm_adapter.backend.huggingface import HuggingFaceBackend

			return HuggingFaceBackend(hyperparams=hyperparams, token=HF_TOKEN)
		if backend_name == "deepseek":
			if not OPENROUTER_API_KEY:
				raise ValueError("OPENROUTER_API_KEY environment variable is required for DeepSeek models")
			from CybORG.Agents.LLMAgents.llm_adapter.backend.deepseek import DeepSeekBackend

			return DeepSeekBackend(hyperparams=hyperparams, api_key=OPENROUTER_API_KEY)
		if backend_name == "ollama":
			from CybORG.Agents.LLMAgents.llm_adapter.backend.ollama import OllamaBackend

			return OllamaBackend(hyperparams=hyperparams)
		if backend_name == "dummy":
			from CybORG.Agents.LLMAgents.llm_adapter.backend.dummy import DummyBackend

			return DummyBackend()
		raise ValueError(f"Invalid backend: {backend_name}")


class ModelManager:
	"""Model manager for chat-completion backends.

	The manager centralizes backend selection and provides structured-output
	utilities so downstream policies can request a JSON-like action/reason pair
	and fall back safely when the model drifts away from the requested format.
	"""

	STRUCTURED_OUTPUT_INSTRUCTION = (
		"Return a valid JSON object with exactly two keys: action and reason. "
		"The action value must be one of the allowed defense actions with its parameter. "
		"The reason value must be a short explanation. Return JSON only."
	)

	ACTION_SYNONYMS: dict[str, list[str]] = {
		"remove": ["remove"],
		"restore": ["restore"],
		"blocktrafficzone": ["blocktrafficzone", "block traffic zone", "block traffic"],
		"allowtrafficzone": ["allowtrafficzone", "allow traffic zone", "allow traffic"],
		"deploydecoy": ["deploydecoy", "deploy decoy", "decoy"],
		"analyse": ["analyse", "analyze", "analysis"],
		"sleep": ["sleep", "wait", "idle", "none", "no action"],
	}

	def __init__(self, hyperparams: dict):
		self.hyperparams = hyperparams
		self.backend_name = hyperparams["backend"].lower()
		self.model_backend = BackendFactory.create_backend(self.backend_name, hyperparams)
		self.enable_schema_constraints = hyperparams.get("schema_constraints", True)
		self.enable_self_correction = hyperparams.get("self_correction", True)
		self.enable_preventative_cosc = hyperparams.get("preventative_cosc", True)
		self.max_repair_attempts = int(hyperparams.get("repair_attempts", 1))
		self.hallucination_metrics: dict[str, int] = {
			"syntactic_hallucination_count": 0,
			"semantic_hallucination_count": 0,
			"repair_attempt_count": 0,
			"repair_success_count": 0,
			"fallback_sleep_count": 0,
			"total_structured_calls": 0,
		}

	def get_hallucination_metrics(self) -> dict[str, int]:
		return dict(self.hallucination_metrics)

	def reset_hallucination_metrics(self):
		for key in self.hallucination_metrics:
			self.hallucination_metrics[key] = 0

	def generate_response(self, message: List[Dict[str, str]]) -> str:
		"""Generates a free-form response using the selected backend."""
		try:
			return self.model_backend.generate(message)
		except Exception:
			# Keep evaluation running even if model endpoint is unavailable.
			return '{"action": "Sleep", "reason": "Model request failed; defaulted to Sleep."}'

	def generate_structured_response(self, message: List[Dict[str, str]]) -> Dict[str, str]:
		"""Generates a structured response with action/reason keys, with intelligent fallback pool."""
		self.hallucination_metrics["total_structured_calls"] += 1
		structured_messages = self._inject_structure_instruction(message)
		ioc_priorities = self._extract_ioc_priorities_from_messages(structured_messages)
		raw_response = self.generate_response(structured_messages)
		parsed_response = self._parse_structured_payload(raw_response)
		if parsed_response is not None:
			is_valid, feedback = self._validate_action_against_ioc(parsed_response.get("action", ""), ioc_priorities)
			if is_valid:
				return parsed_response
			self.hallucination_metrics["semantic_hallucination_count"] += 1
			raw_response = json.dumps(parsed_response)
		else:
			self.hallucination_metrics["syntactic_hallucination_count"] += 1
			feedback = "Invalid response structure."

		if self.enable_self_correction:
			for _ in range(self.max_repair_attempts):
				self.hallucination_metrics["repair_attempt_count"] += 1
				repair_messages = copy.deepcopy(structured_messages)
				repair_messages.append({"role": "assistant", "content": raw_response})
				repair_messages.append({
					"role": "user",
					"content": (
						"The previous response was invalid. Rewrite it as STRICT JSON with exactly "
						"two keys: action and reason. Do not use markdown, bullets, code fences, or extra keys. "
						"Use only one allowed action and include host:<hostname> or subnet:<subnet_id> when required. "
						f"Semantic verification feedback: {feedback}"
					),
				})
				raw_response = self.generate_response(repair_messages)
				parsed_response = self._parse_structured_payload(raw_response)
				if parsed_response is not None:
					is_valid, feedback = self._validate_action_against_ioc(
						parsed_response.get("action", ""), ioc_priorities
					)
					if is_valid:
						self.hallucination_metrics["repair_success_count"] += 1
						return parsed_response
					self.hallucination_metrics["semantic_hallucination_count"] += 1
				else:
					self.hallucination_metrics["syntactic_hallucination_count"] += 1

		# Intelligent fallback pool: try to infer a reasonable action from raw response
		inferred = self._infer_fallback_action(raw_response)
		if inferred:
			return inferred
		
		self.hallucination_metrics["fallback_sleep_count"] += 1
		return {"action": "Sleep", "reason": "Model output was invalid; defaulted to Sleep."}

	def _extract_ioc_priorities_from_messages(self, messages: List[Dict[str, str]]) -> dict[str, int]:
		"""Extract host IOC priorities from formatted observation text in recent user messages."""
		host_priorities: dict[str, int] = {}
		for msg in reversed(messages):
			if msg.get("role") != "user":
				continue
			content = str(msg.get("content", ""))
			if "# IOC SUMMARY" not in content:
				continue
			for line in content.splitlines():
				line = line.strip()
				match = re.search(r"Host:\s*([^|]+)\|.*IOC Priority:\s*(\d+)", line)
				if not match:
					continue
				host = match.group(1).strip().lower()
				prio = int(match.group(2))
				host_priorities[host] = prio
			if host_priorities:
				break
		return host_priorities

	def _validate_action_against_ioc(self, action: str, host_ioc: dict[str, int]) -> tuple[bool, str]:
		"""Preventative CoSC semantic validation using IOC-guided rules."""
		if not self.enable_preventative_cosc:
			return True, "Preventative CoSC disabled."
		if not action:
			return False, "Missing action field."
		if not host_ioc:
			return True, "No IOC summary available for semantic validation."

		action_l = action.lower()
		host_match = re.search(r"host\s*:\s*([a-z0-9_\-\.]+)", action_l)
		target_host = host_match.group(1).strip().lower() if host_match else None

		severe_hosts = [h for h, p in host_ioc.items() if p >= 2]
		any_ioc = any(p >= 1 for p in host_ioc.values())

		if severe_hosts and not any(token in action_l for token in ("remove", "restore")):
			severe_host = severe_hosts[0]
			return (
				False,
				f"Severe IOC detected on {severe_host}. Must use Remove/Restore on severe IOC host.",
			)

		if any(token in action_l for token in ("remove", "restore")):
			if not target_host:
				return False, "Remove/Restore requires host:<hostname> target."
			host_prio = host_ioc.get(target_host)
			if host_prio is None:
				return False, f"Target host {target_host} not found in IOC summary."
			if host_prio < 2:
				return False, f"Target host {target_host} IOC priority is {host_prio}; recovery is not justified."

		if not any_ioc and any(token in action_l for token in ("remove", "restore")):
			return False, "No IOC detected; avoid recovery actions on clean state."

		return True, "Semantic IOC validation passed."

	def _infer_fallback_action(self, raw_response: str) -> dict[str, str] | None:
		"""Attempt to infer a valid action from raw LLM response text.
		
		Useful for recovering from parse failures by pattern-matching common action names.
		Returns a dict with "action" and "reason" keys, or None if inference fails.
		"""
		if not raw_response or not isinstance(raw_response, str):
			return None
		
		response_lower = raw_response.lower()
		
		# Common keywords mapped to fallback actions
		action_keywords = {
			"remove": "Remove",
			"restore": "Restore",
			"block": "BlockTrafficZone",
			"allow": "AllowTrafficZone",
			"deploy": "DeployDecoy",
			"analyse": "Analyse",
			"analyze": "Analyse",
			"sleep": "Sleep",
		}
		
		for keyword, action in action_keywords.items():
			if keyword in response_lower:
				return {"action": action, "reason": "Inferred from response text after parse failure."}
		
		return None

	def _inject_structure_instruction(self, message: List[Dict[str, str]]) -> List[Dict[str, str]]:
		messages = copy.deepcopy(message)
		if not self.enable_schema_constraints:
			return messages

		instruction = {"role": "system", "content": self.STRUCTURED_OUTPUT_INSTRUCTION}
		if messages and messages[0].get("role") == "system":
			messages[0]["content"] = f"{messages[0].get('content', '')}\n\n{self.STRUCTURED_OUTPUT_INSTRUCTION}"
		else:
			messages.insert(0, instruction)
		return messages

	def _parse_structured_payload(self, response: Any) -> Dict[str, str] | None:
		if isinstance(response, Mapping):
			action = str(response.get("action", "")).strip()
			reason = str(response.get("reason", "")).strip()
			if action:
				action_cleaned = self._normalize_action(action)
				if action_cleaned:
					return {"action": action_cleaned, "reason": reason}
			return None

		if not isinstance(response, str):
			return None

		text = response.strip()
		if not text:
			return None

		json_candidates = [text]
		json_candidates.extend(match.group(0) for match in re.finditer(r"\{.*?\}", text, re.DOTALL))

		for candidate in json_candidates:
			for parser in (json.loads, ast.literal_eval):
				try:
					parsed = parser(candidate)
					if isinstance(parsed, Mapping):
						action = str(parsed.get("action", "")).strip()
						reason = str(parsed.get("reason", "")).strip()
						if action:
							action_cleaned = self._normalize_action(action)
							if action_cleaned:
								return {"action": action_cleaned, "reason": reason}
				except Exception:
					continue

		action_match = re.search(r"action\s*[:=]\s*([^\n,}]+)", text, re.IGNORECASE)
		reason_match = re.search(r"reason\s*[:=]\s*([^\n,}]+)", text, re.IGNORECASE)
		if action_match:
			action = action_match.group(1).strip().strip("\"'")
			reason = reason_match.group(1).strip().strip("\"'") if reason_match else ""
			return {"action": action, "reason": reason}

		heuristic = self._extract_action_heuristic(text)
		if heuristic:
			return heuristic

		return None

	def _normalize_action(self, action_str: str) -> str | None:
		"""Normalize and validate action strings; strip markdown/formatting and extract canonical action.
		
		Returns the action name (e.g., 'Remove host:HOSTNAME') or None if invalid.
		"""
		# Clean markdown and excessive whitespace
		clean = action_str.lower().replace("`", " ").replace("*", " ")
		clean = re.sub(r"\s+", " ", clean).strip()
		
		# Try to match against known action synonyms
		for canonical, aliases in self.ACTION_SYNONYMS.items():
			for alias in aliases:
				if alias in clean:
					# Extract parameters from original action_str (to preserve case/format)
					host_match = re.search(r"host\s*:\s*([a-z0-9_\-\.]+)", clean, re.IGNORECASE)
					subnet_match = re.search(r"subnet\s*:\s*([a-z0-9_\-\.]+)", clean, re.IGNORECASE)
					hostname = host_match.group(1) if host_match else None
					subnet_id = subnet_match.group(1) if subnet_match else None
					
					# Return formatted action with proper capitalization
					action_name = canonical
					if action_name == "blocktrafficzone":
						action_name = "BlockTrafficZone"
					elif action_name == "allowtrafficzone":
						action_name = "AllowTrafficZone"
					elif action_name == "deploydecoy":
						action_name = "DeployDecoy"
					elif action_name == "sleep":
						action_name = "Sleep"
					else:
						action_name = action_name.capitalize()
					
					# Append parameters if present
					if hostname:
						return f"{action_name} host:{hostname}"
					elif subnet_id:
						return f"{action_name} subnet:{subnet_id}"
					else:
						return action_name
		
		return None

	def _extract_action_heuristic(self, text: str) -> Dict[str, str] | None:
		"""Recover action/reason from non-JSON model replies."""
		clean_text = text.lower().replace("`", " ").replace("*", " ")
		clean_text = re.sub(r"\s+", " ", clean_text).strip()

		host_match = re.search(r"host\s*:\s*([a-z0-9_\-\.]+)", clean_text)
		subnet_match = re.search(r"subnet\s*:\s*([a-z0-9_\-\.]+)", clean_text)
		hostname = host_match.group(1) if host_match else None
		subnet = subnet_match.group(1) if subnet_match else None

		for canonical, aliases in self.ACTION_SYNONYMS.items():
			if any(alias in clean_text for alias in aliases):
				if canonical == "remove" and hostname:
					return {"action": f"Remove host:{hostname}", "reason": "Recovered from non-JSON response."}
				if canonical == "restore" and hostname:
					return {"action": f"Restore host:{hostname}", "reason": "Recovered from non-JSON response."}
				if canonical == "deploydecoy" and hostname:
					return {"action": f"DeployDecoy host:{hostname}", "reason": "Recovered from non-JSON response."}
				if canonical == "analyse" and hostname:
					return {"action": f"Analyse host:{hostname}", "reason": "Recovered from non-JSON response."}
				if canonical == "blocktrafficzone" and subnet:
					return {"action": f"BlockTrafficZone subnet:{subnet}", "reason": "Recovered from non-JSON response."}
				if canonical == "allowtrafficzone" and subnet:
					return {"action": f"AllowTrafficZone subnet:{subnet}", "reason": "Recovered from non-JSON response."}
				if canonical == "sleep":
					return {"action": "Sleep", "reason": "Recovered from non-JSON response."}

		return None

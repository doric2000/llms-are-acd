from __future__ import annotations

import ast
import copy
import json
import os
import re
from typing import Any, Dict, List, Mapping

from CybORG.Agents.LLMAgents.llm_adapter.backend.deepseek import DeepSeekBackend
from CybORG.Agents.LLMAgents.llm_adapter.backend.dummy import DummyBackend
from CybORG.Agents.LLMAgents.llm_adapter.backend.huggingface import HuggingFaceBackend
from CybORG.Agents.LLMAgents.llm_adapter.backend.model_backend import ModelBackend
from CybORG.Agents.LLMAgents.llm_adapter.backend.ollama import OllamaBackend
from CybORG.Agents.LLMAgents.llm_adapter.backend.openai import NewOpenAIBackend
from CybORG.Agents.LLMAgents.llm_adapter.backend.openai import OpenAIBackend


HF_TOKEN = os.environ.get("HF_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

class BackendFactory:
    """Factory class for creating model backend instances."""

    @staticmethod
    def create_backend(backend_name: str, hyperparams: dict) -> ModelBackend:
        if backend_name == "openai":
            return OpenAIBackend(hyperparams=hyperparams, api_key=OPENAI_API_KEY)
        elif backend_name == "huggingface":
            return HuggingFaceBackend(hyperparams=hyperparams, token=HF_TOKEN)
        elif backend_name == "new-openai":
            return NewOpenAIBackend(hyperparams=hyperparams, api_key=OPENAI_API_KEY)
        elif backend_name == "deepseek":
            if not OPENROUTER_API_KEY:
                    raise ValueError("OPENROUTER_API_KEY environment variable is required for DeepSeek models")
            return DeepSeekBackend(hyperparams=hyperparams, api_key=OPENROUTER_API_KEY)
        elif backend_name == "ollama":
            return OllamaBackend(hyperparams=hyperparams)
        elif backend_name == "dummy":
            return DummyBackend()
        else:
            raise ValueError(f"Invalid backend: {backend_name}")

class ModelManager:
    """Model manager class.
    
    This class is responsible for managing the model backend instances, sending messages to the model backend,
    handling the responses, and storing the model configurations.
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
        self.max_repair_attempts = int(hyperparams.get("repair_attempts", 1))
    
    def generate_response(self, message: List[Dict[str, str]]) -> str:
        """Generates a response using the model backend."""
        try:
            return self.model_backend.generate(message)
        except Exception:
            return '{"action": "Sleep", "reason": "Model request failed; defaulted to Sleep."}'

    def generate_structured_response(self, message: List[Dict[str, str]]) -> Dict[str, str]:
        """Generates a structured response with action and reason keys."""
        structured_messages = self._inject_structure_instruction(message)
        raw_response = self.generate_response(structured_messages)
        parsed_response = self._parse_structured_payload(raw_response)
        if parsed_response is not None:
            return parsed_response

        if self.enable_self_correction:
            for _ in range(self.max_repair_attempts):
                repair_messages = copy.deepcopy(structured_messages)
                repair_messages.append({"role": "assistant", "content": raw_response})
                repair_messages.append({
                    "role": "user",
                    "content": (
                        "The previous response was invalid. Rewrite it as STRICT JSON with exactly "
                        "two keys: action and reason. Do not use markdown, bullets, code fences, or extra keys. "
                        "Use only one allowed action and include host:<hostname> or subnet:<subnet_id> when required."
                    ),
                })
                raw_response = self.generate_response(repair_messages)
                parsed_response = self._parse_structured_payload(raw_response)
                if parsed_response is not None:
                    return parsed_response

        return {"action": "Sleep", "reason": "Model output was invalid; defaulted to Sleep."}

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
            action = action_match.group(1).strip().strip('"\'')
            reason = reason_match.group(1).strip().strip('"\'') if reason_match else ""
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

    def _infer_fallback_action(self, text: str) -> Dict[str, str] | None:
        """Infer a reasonable action from raw model response when all parsing fails.
        
        Fallback pool: tries Analyse (gather intel) → Sleep (hold) if no host identified
        """
        clean = text.lower().replace("`", " ").replace("*", " ")
        clean = re.sub(r"\s+", " ", clean).strip()
        
        # Extract any hostname or subnet mention from the raw text
        host_match = re.search(r"host\s*:\s*([a-z0-9_\-\.]+)", clean, re.IGNORECASE)
        subnet_match = re.search(r"subnet\s*:\s*([a-z0-9_\-\.]+)", clean, re.IGNORECASE)
        hostname = host_match.group(1) if host_match else None
        subnet_id = subnet_match.group(1) if subnet_match else None
        
        # Strategy: if we mention a hostname, try Analyse (free intel gathering)
        if hostname:
            return {"action": f"Analyse host:{hostname}", "reason": "Fallback: gathering intelligence on suspicious host."}
        
        # If no specific target, wait (Sleep is safest)
        return {"action": "Sleep", "reason": "Fallback: insufficient context to act defensively."}
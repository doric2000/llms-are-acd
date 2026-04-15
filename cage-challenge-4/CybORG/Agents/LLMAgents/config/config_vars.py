import os

# Submission Information
SUB_NAME = "LLM and RL Agent"
SUB_TEAM = "UCSC Autonomous Cybersecurity Lab"
SUB_TECHNIQUE = "LLM+RL"

# LLM Agent
# Can be set to `blue_agent_0` or `blue_agent_1` or `blue_agent_2` or `blue_agent_3` or `blue_agent_4`
BLUE_AGENT_NAME = "blue_agent_4"
ALL_LLM_AGENTS = False              # DANGER: Do you want all the LLM agents to play?
NO_LLM_AGENTS = False               # Do not enable both at the same time!

# Config files
CONFIG_MODEL_PATH = "config/model/ollama-deepseek-r1-8b.yml"
STRATEGY_PROMPT_PATH = "config/prompts/acd2025/base.yml"                  # Strategy prompt loaded second

# Environment variables
ENV_VAR_MODEL = "CAGE4_MODEL_CONFIG"
ENV_VAR_PROMPT = "CAGE4_PROMPTS_CONFIG"

# Prompt Variables
INCLUDE_PROMPT_CAGE4_RULES = False         # Include the rules of Cage 4 in the prompt
INCLUDE_PROMPT_COMMVECTOR_RULES = False    # Include the commvector rules in the prompt
COMMVECTOR_RULES_PROMPT_PATH = "config/prompts/env_rules/commvector_rules.yml"
CAGE4_RULES_PROMPT_PATH = "config/prompts/env_rules/cage4_rules_v2.yml"   # Always loaded first

# Extra
DEBUG_MODE = os.environ.get("CAGE4_DEBUG_MODE", "false").lower() in {"1", "true", "yes", "on"}
TOTAL_STEPS_PROGRESS_BAR = 1000

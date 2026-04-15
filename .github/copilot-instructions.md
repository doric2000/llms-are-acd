# Copilot Instructions for This Repo

## Project shape
- This repository is the CAGE Challenge 4 / CybORG autonomous cyber-defense codebase.
- The main challenge package lives under `cage-challenge-4/CybORG/`; top-level `README.md` and `cage-challenge-4/README.md` describe the intended workflows.
- Core scenarios use `EnterpriseScenarioGenerator` with `SleepAgent`, `EnterpriseGreenAgent`, and a red agent such as `FiniteStateRedAgent`.

## Agent and submission contract
- Evaluation loads a `Submission` class from a directory or zip via `cage-challenge-4/CybORG/Evaluation/evaluation.py`.
- A submission must expose `NAME`, `TEAM`, `TECHNIQUE`, and an `AGENTS` dict keyed like `blue_agent_0` ... `blue_agent_4`.
- `Submission.wrap(env)` must return a compatible wrapper, usually a `MultiAgentEnv` or a CybORG wrapper such as `EnterpriseMAE`.
- Custom agents should inherit from `CybORG.Agents.BaseAgent` and implement `get_action()`; the examples in `cage-challenge-4/CybORG/Evaluation/*/submission.py` are the best templates.

## Environment and wrappers
- `cage-challenge-4/CybORG/Agents/Wrappers/EnterpriseMAE.py` is the canonical multi-agent wrapper for blue-team evaluation.
- Cybermonic agents use `GraphWrapper` and `ObservationGraph` from `cage-challenge-4/CybORG/Agents/Wrappers/CybermonicWrappers/` to turn observations into graph features.
- The LLMAgent path uses `PhaseWrapper`/`CombinedWrapper` logic in `cage-challenge-4/CybORG/Evaluation/llamagym/submission.py` to merge phase info, comm-vectors, and graph observations.

## LLM agent conventions
- `cage-challenge-4/CybORG/Agents/LLMAgents/llm_policy.py` expects model output shaped like a dictionary with `action` and `reason` keys.
- Supported blue actions in that policy are: `Remove`, `Restore`, `BlockTrafficZone`, `AllowTrafficZone`, `DeployDecoy`, `Analyse`, and `Sleep`.
- If parsing fails or the response is invalid, the policy deliberately falls back to `Sleep`.
- LLM configuration is driven by `cage-challenge-4/CybORG/Agents/LLMAgents/config/config_vars.py` and env vars `CAGE4_MODEL_CONFIG` / `CAGE4_PROMPTS_CONFIG`.
- `ALL_LLM_AGENTS` and `NO_LLM_AGENTS` are mutually exclusive toggles; the default setup usually mixes one LLM defender with learned or heuristic defenders.

## Cybermonic training path
- `cybermonic_train.py` trains graph-based defenders and saves logs to `logs/` and checkpoints to `checkpoints/`.
- It uses `GraphWrapper`, `InductiveGraphPPOAgent`, `wandb`, and multiprocessing/joblib for episode generation.
- When changing graph features, keep `cybermonic_train.py`, `GraphWrapper`, and `ObservationGraph.DIM` in sync.

## Developer workflow
- Activate the repo environment before running anything: `source cage-env/bin/activate`.
- LLM workflows also need API keys sourced from `.env`; several scripts assume `OPENAI_API_KEY` and/or `OPENROUTER_API_KEY` are present.
- Useful validation commands are `python verify_imports.py`, `python test_cyborg.py`, and `python -m CybORG.Evaluation.evaluation --max-eps 2 <submission> <output>`.
- For docs work, `cd cage-challenge-4/documentation && mkdocs serve` starts the local site.

## Editing conventions
- Keep changes localized to the relevant path under `cage-challenge-4/CybORG/` unless you are updating the top-level helper scripts or docs.
- When modifying prompts, action names, or wrappers, update the parser, prompt YAML, and wrapper logic together.
- Prefer small, concrete changes that preserve the existing agent interfaces and submission format.

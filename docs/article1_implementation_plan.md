# Article 1 Implementation Plan

Source article: Large Language Models are Autonomous Cyber Defenders (arXiv:2505.04843v2)

## Extracted Experimental Constants (must match)

- Environment: CybORG CAGE 4
- Episodes per run: 2
- Steps per episode: 500
- Green policy: EnterpriseGreenAgent
- Blue-team scenarios:
  - No blue agents (all Sleep)
  - All blue agents as LLM
  - All blue agents as RL (KEEP)
  - 1 LLM + 4 RL (LLM at blue_agent_4)
- Red strategies to evaluate:
  - FiniteStateRedAgent (default baseline)
  - AggressiveFSMAgent
  - StealthyFSMAgent
  - ImpactFSMAgent
  - DegradeServiceFSMAgent
- Metrics to report:
  - Mean joint reward (mu)
  - Reward standard deviation (sigma)
  - Runtime per configuration
- Requirement from our research constraints:
  - Keep our model set unchanged (model list is configurable input, not hard-coded by this plan)

## Environment Lock Policy

Add a single source of truth for experiment constants and enforce it before every run.

1. Create an experiment profile object (or YAML) with:
   - max_eps=2
   - episode_length=500
   - green_agent=EnterpriseGreenAgent
   - red_agents list above
   - blue_modes list above
2. Add a preflight validator that fails fast if runtime args differ from profile.
3. Persist the effective profile in every output directory as run_profile.json.
4. Add a post-run checker that asserts each produced result used the same profile.

## Phase 2 (Preventative CoSC) - Article-aligned implementation

Goal: enforce valid action selection before action commit.

1. Prompt changes:
   - Require strict action feasibility check in the response protocol.
   - Keep output schema: action + reason.
2. Model manager changes:
   - Add a verification loop after parse but before action return.
   - Implement contradiction guards (host/subnet/action consistency checks).
   - On contradiction, ask model to regenerate once per configured retry policy.
3. Policy integration:
   - In policy action extraction, treat failed verification as invalid action and route to fallback.
4. Metrics hooks:
   - Track verification_failures, repaired_actions, fallback_actions.

## Phase 3 (Systematic Evaluation Protocol)

Goal: reproduce article evaluation matrix while keeping our models.

1. Add red-agent sweep support to evaluation runner.
2. Add blue-mode sweep support (no-blue, all-LLM, all-RL, mixed 1+4).
3. Keep models as user-provided list (do not replace model family).
4. Build full matrix:
   - models x blue_modes x red_agents x 2 episodes x 500 steps
5. Aggregate outputs:
   - reward mu/sigma, runtime
   - per-red-agent summary
   - per-blue-mode summary

## Phase 4 (Reasoning Analysis)

Goal: quantify action-reason behavior during evaluation.

1. Collect action/reason pairs for each step.
2. Add deterministic parsing and quality flags for reasons.
3. Produce analysis report:
   - reason frequency by action type
   - contradiction rate by red strategy
   - fallback reason distribution
4. Keep this phase non-invasive to agent policy behavior.

## Required File Touchpoints

- CybORG/Agents/LLMAgents/llm_adapter/model_manager.py
- CybORG/Agents/LLMAgents/llm_policy.py
- CybORG/Evaluation/llamagym/run_model_comparison.py
- cage-challenge-4/CybORG/Evaluation/evaluation.py
- prompt.yml

## Acceptance Checklist (Article 1)

- [ ] Every run logs profile with max_eps=2 and episode_length=500.
- [ ] Green agent is EnterpriseGreenAgent in all runs.
- [ ] Red-agent sweep includes the five strategies listed above.
- [ ] Blue-mode sweep includes all four article scenarios.
- [ ] Model list remains our own selected models.
- [ ] Results include mu, sigma, runtime for each matrix cell.
- [ ] Phase 2 verification metrics are emitted.
- [ ] Phase 4 reasoning report is generated.

## Immediate Execution Order

1. Implement environment lock + run_profile persistence.
2. Implement preventative CoSC loop.
3. Implement evaluation sweeps and aggregation.
4. Implement reasoning analysis pipeline.
5. Run a small smoke test, then full article profile run.

# Project Delta from Original `llms-are-acd`

This document summarizes the main extension points in this repository relative to the upstream project.

- Upstream reference: [r4wd3r/llms-are-acd](https://github.com/r4wd3r/llms-are-acd.git)
- Goal of this delta: preserve the original architecture while adding a small, novel research extension around reliability, reproducibility, and model comparison.

## 1) LLM Adapter and Policy Logic

### What Was Added
- Preventative semantic verification (CoSC-style gating) before action commit.
- Hallucination-related counters and structured repair/fallback behavior.
- IOC-priority and topology-aware observation formatting.
- Additional backend support for local inference flows.

### Where
- `CybORG/Agents/LLMAgents/llm_adapter/model_manager.py`
- `CybORG/Agents/LLMAgents/llm_adapter/obs_formatter.py`
- `CybORG/Agents/LLMAgents/llm_adapter/backend/ollama.py`
- `CybORG/Agents/LLMAgents/llm_adapter/metrics_tracker.py`
- `CybORG/Agents/LLMAgents/llm_policy.py`

### Why It Matters
- Reduces malformed or semantically contradictory actions.
- Makes agent behavior auditable through explicit hallucination/repair telemetry.
- Improves reasoning context quality by making host compromise signals explicit.

## 2) Evaluation and Experiment Orchestration

### What Was Added
- Profile-driven execution (`quick` and `strict`) with reproducibility metadata.
- Matrix execution for paper-style case sweeps (red variants and scenario seeds).
- Extended report generation and structured outputs per model/per case.

### Where
- `CybORG/Evaluation/llamagym/run_model_comparison.py`
- `cage-challenge-4/CybORG/Evaluation/evaluation.py`
- `CybORG/Evaluation/Cybermonics/submission.py`

### Why It Matters
- Prevents configuration drift in experiments.
- Enables controlled cross-model comparisons under consistent protocol.
- Produces repeatable artifacts suitable for paper reporting.

## 3) Model and Prompt Configuration Surface

### What Was Added
- Additional model configs for local and comparison-focused runs.
- Prompt/configuration updates supporting stricter structured output behavior.

### Where
- `CybORG/Agents/LLMAgents/config/model/`
- `cage-challenge-4/CybORG/Agents/LLMAgents/config/model/`
- `cage-challenge-4/CybORG/Agents/LLMAgents/config/prompts/`

### Why It Matters
- Makes the framework practical for local reproducible experimentation.
- Supports controlled model swaps without code-path rewrites.

## 4) Result Artifacts and Analysis Outputs

### What Was Added
- Canonical matrix outputs and case-level artifacts for DeepSeek and Qwen runs.
- Combined comparison outputs against original-paper baselines.
- Visualization-ready files and supporting tables.

### Where
- `results/paper_parity_matrix/deepseek_steps1_7_plus_step8_20260416/`
- `results/paper_parity_matrix/qwen_full_30x30_20260416/`
- `results/paper_parity_matrix/final_combined_20260416/`

### Why It Matters
- Keeps a full audit trail (`summary.json`, `run_profile.json`, traces, logs).
- Separates execution artifacts from narrative claims for reproducibility.

## 5) Documentation and Operational Guides

### What Was Added
- Detailed implementation changelog and reproducibility guides.
- Practical docs for strict comparison runs and parity interpretation.
- Script and plotting organization into dedicated folders.

### Where
- `docs/IMPLEMENTATION_CHANGELOG.md`
- `docs/README_EXPERIMENT_IMPROVEMENTS.md`
- `docs/RUN_CYBERMONICS_COMPARISON.md`
- `shell_scripts/`
- `plot_scripts/`

### Why It Matters
- Lowers onboarding friction for reruns.
- Keeps top-level README concise while preserving technical depth in focused docs.

## 6) Scope Notes

- This repository includes substantial generated artifacts and runtime outputs.
- Not every file delta reflects a novel algorithmic contribution; key novelty is concentrated in:
  - LLM semantic hardening (CoSC-style logic),
  - Reproducibility protocol and matrix orchestration,
  - Expanded defense/hallucination telemetry.

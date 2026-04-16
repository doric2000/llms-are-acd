# Micro-Level Change Log (vs Original Project)

This document provides a file-level view of what was changed, added, or upgraded in this repository relative to the original `llms-are-acd` baseline.

Use this as the detailed companion to:
- `README.md` (high-level overview)
- `docs/PROJECT_DELTA_FROM_ORIGINAL.md` (subsystem-level summary)

## Scope

- Focus: changes that improve **robustness**, **reproducibility**, and **evaluation quality** for LLM-based cyber defense agents.
- Source of truth for step history: `docs/IMPLEMENTATION_CHANGELOG.md`.

## 1) LLM Adapter and Policy: Micro Changes

### Added
- `CybORG/Agents/LLMAgents/llm_adapter/metrics_tracker.py`
- `cage-challenge-4/CybORG/Agents/LLMAgents/llm_adapter/metrics_tracker.py`
  - Adds interpretable defense metric helpers and aggregation utilities.

- `CybORG/Agents/LLMAgents/llm_adapter/backend/ollama.py`
- `cage-challenge-4/CybORG/Agents/LLMAgents/llm_adapter/backend/ollama.py`
  - Adds local Ollama backend support for self-hosted model execution.

### Upgraded
- `CybORG/Agents/LLMAgents/llm_adapter/model_manager.py`
- `cage-challenge-4/CybORG/Agents/LLMAgents/llm_adapter/model_manager.py`
  - Added preventative CoSC semantic validation (`_extract_ioc_priorities_from_messages`, `_validate_action_against_ioc`).
  - Added hallucination taxonomy counters (syntactic/semantic/repair/fallback counters).
  - Added robust fallback action inference (`_infer_fallback_action`) for malformed output recovery.

- `CybORG/Agents/LLMAgents/llm_adapter/obs_formatter.py`
- `cage-challenge-4/CybORG/Agents/LLMAgents/llm_adapter/obs_formatter.py`
  - Added structured `# NETWORK TOPOLOGY` and `# IOC SUMMARY` output sections.
  - Improved commvector handling robustness for iterable/numpy-like inputs.

- `CybORG/Agents/LLMAgents/llm_policy.py`
- `cage-challenge-4/CybORG/Agents/LLMAgents/llm_policy.py`
  - Fixed episode boundary logging behavior.
  - Uses dynamic progress totals (`max_eps * episode_length`).
  - Adds step-level trace resilience via defensive path fallback logic.

### Improvement Impact
- Fewer invalid/contradictory LLM actions.
- Better observability into why actions fail or self-correct.
- More stable long/matrix runs under noisy model output conditions.

## 2) Evaluation and Orchestration: Micro Changes

### Added
- `CybORG/Evaluation/llamagym/run_model_comparison.py`
  - Added profile mode (`quick`, `strict`) and profile persistence.
  - Added matrix execution (`--matrix`, red variants, scenario seeds).
  - Added case-level metadata and richer comparison reporting.

### Upgraded
- `cage-challenge-4/CybORG/Evaluation/evaluation.py`
  - Strict baseline guard and profile environment validation.
  - Profile metadata written to outputs (`summary.json`, `run_profile.json`).
  - Alias support for paper red-agent terms (`b_line`, `meander`).

- `cage-challenge-4/CybORG/Shared/MetricsCallback.py`
  - Added per-step reward/cumulative reward trace persistence.

- `cage-challenge-4/CybORG/Evaluation/llamagym/submission.py`
  - Passes reward stream to metrics callback for trace output.

- `CybORG/Evaluation/Cybermonics/submission.py`
  - Updated integration path for 1 LLM + 4 RL (KEEP) comparison runs.

### Improvement Impact
- Reproducible execution protocol with lower configuration drift.
- Direct paper-style matrix runs with structured metadata per case.
- Better auditability and post-run analysis quality.

## 3) Model and Prompt Config Surface: Micro Changes

### Added
- `CybORG/Agents/LLMAgents/config/model/deepseek-r1-1.5b.yml`
- `CybORG/Agents/LLMAgents/config/model/qwen2.5-7b.yml`
- `CybORG/Agents/LLMAgents/config/model/gemma4-e4b.yml`
- (Parallel additions mirrored under `cage-challenge-4/CybORG/Agents/LLMAgents/config/model/`)

### Upgraded
- `CybORG/Agents/LLMAgents/config/config_vars.py`
- `CybORG/Agents/LLMAgents/config/model/*.yml` (existing model files updated)
  - Tuned default model selection and runtime config behavior for comparison experiments.

### Improvement Impact
- Easier local benchmarking across current model families.
- Cleaner model swap workflow without code-path rewrites.

## 4) Metrics and Telemetry Exports: Micro Changes

### Added
- Hallucination metrics fields in run summaries:
  - syntactic/semantic counts, repair attempts/successes, fallback counts, hallucination rate.
- Defense metrics fields:
  - recovery precision/error, clean-host ratio, MTTR approximation, red impact count.

### Upgraded
- Comparison report schema to include hallucination-oriented columns and profile metadata.
- Per-case artifact completeness (`summary`, `scores`, actions/full logs, run profile, traces).

### Improvement Impact
- Moves evaluation from reward-only analysis to behavior-quality analysis.
- Supports academic claims with richer and inspectable evidence.

## 5) Experiment Artifacts and Reporting Layout

### Added
- `results/paper_parity_matrix/deepseek_steps1_7_plus_step8_20260416/`
- `results/paper_parity_matrix/qwen_full_30x30_20260416/`
- `results/paper_parity_matrix/final_combined_20260416/`
  - Includes per-case outputs, combined summaries, and figure/table-ready artifacts.

### Improvement Impact
- Preserves reproducible experiment history and report-ready outputs.
- Enables transparent comparison against original paper baselines.

## 6) Scripts and Documentation Structure Improvements

### Added
- `docs/PROJECT_DELTA_FROM_ORIGINAL.md` (subsystem-level delta)
- `docs/README_MICRO_CHANGES.md` (this file, file-level delta)

### Upgraded
- Script organization:
  - moved run scripts to `shell_scripts/`
  - plotting utility moved to `plot_scripts/`
- Script root resolution:
  - `shell_scripts/run_cybermonics_strict.sh`
  - `shell_scripts/run_cybermonics_comparison.sh`
  - updated `REPO_ROOT` resolution to work after folder move.

### Improvement Impact
- Cleaner repository structure and discoverability.
- Fewer path-related execution failures after reorganization.

## Quick Improvement Summary

- Added preventative semantic CoSC checks and stronger fallback behavior.
- Upgraded observation formatting to include IOC-priority and topology context.
- Added strict reproducibility profiles and paper-matrix orchestration.
- Added hallucination and interpretable defense metrics for deeper evaluation.
- Improved script/doc organization for easier reuse and onboarding.

# Beyond the Baseline: LLM-Driven Autonomous Cyber Defense

This repository is an extended fork of the original `llms-are-acd` project by Castro et al., with additional implementation and experiments for our follow-up paper.

It is also part of the course project **Advanced Subjects In Cyber Protection**. The project focuses on understanding how cyber-defense agents are built and how they operate, then replicating, upgrading, and improving relevant research papers on autonomous cyber agents.

- Original repository: [r4wd3r/llms-are-acd](https://github.com/r4wd3r/llms-are-acd.git)
- Original paper: [Large Language Models are Autonomous Cyber Defenders (arXiv:2505.04843)](https://arxiv.org/abs/2505.04843)
- Our paper (this repo): `pdf/LaTeX/LLMRL_Baruh_Dor_2026.pdf`

## What We Added

Compared to the original project, this extension adds a small but concrete research layer focused on hallucination control, reproducibility, and paper-parity evaluation:

- **Chain-of-Self-Correction (CoSC)** with preventative semantic gating before action commit.
- **Schema-constrained action generation** and repair/fallback behavior for malformed outputs.
- **IOC-priority and topology-aware observation formatting** to improve decision quality.
- **Local inference pipeline** (Ollama backend + added model configs such as DeepSeek/Qwen/Gemma variants).
- **Reproducible profile protocol** (`quick` and `strict`) and matrix orchestration for systematic comparisons.
- **Expanded telemetry**: hallucination taxonomy, defense metrics, run profile metadata, and trace artifacts.

## What Changed vs Original (Where and Why)

High-level delta areas:

- **LLM adapter and policy hardening**
  - `CybORG/Agents/LLMAgents/llm_adapter/`
  - `CybORG/Agents/LLMAgents/llm_policy.py`
  - Why: improve robustness, enforce semantic consistency, and reduce invalid/unsafe actions.
- **Evaluation and experiment orchestration**
  - `CybORG/Evaluation/llamagym/run_model_comparison.py`
  - `cage-challenge-4/CybORG/Evaluation/evaluation.py`
  - Why: run paper-style matrices, lock strict parity profiles, and persist reproducibility metadata.
- **Model/config support for local research runs**
  - `CybORG/Agents/LLMAgents/config/model/`
  - Why: compare modern local models under a unified protocol.
- **Experiment outputs and analysis artifacts**
  - `results/paper_parity_matrix/`
  - Why: preserve auditable per-case outputs and combined comparisons.

For a concise subsystem-by-subsystem map (`what`, `where`, `why`), see:
- `docs/PROJECT_DELTA_FROM_ORIGINAL.md`

For a more detailed micro-level file-by-file log (`added`, `upgraded`, and improvement intent), see:
- `docs/README_MICRO_CHANGES.md`

## Key Results Snapshot

Two result tracks are present in this repo and should be interpreted separately:

- **Paper-aligned strict protocol claims (our manuscript)** are documented in `pdf/LaTeX/LLMRL_Baruh_Dor_2026.pdf`.
- **Current combined comparison artifacts** are in:
  - `results/paper_parity_matrix/final_combined_20260416/original_paper_comparison/original_paper_comparison.json`

From that comparison artifact:
- Original paper RL baseline: reward mean `-493.0`
- Original paper all-LLM baseline: reward mean `-2547.2`
- Current work (artifact run): `deepseek-r1-1.5b` reward mean `-3063.00`, `qwen2.5-7b` reward mean `-12.68`

Use these values with protocol/model-context caveats from the docs before drawing direct paper claims.

## Quick Start

From repository root:

```bash
# 1) Activate environment
source cage-env/bin/activate

# 2) Strict paper-style run (1 LLM + 4 KEEP, 2x500)
bash shell_scripts/run_cybermonics_strict.sh deepseek
# or
bash shell_scripts/run_cybermonics_strict.sh qwen
```

For command details and caveats:
- `docs/RUN_CYBERMONICS_COMPARISON.md`
- `docs/README_EXPERIMENT_IMPROVEMENTS.md`

## Repository Map

- `CybORG/Agents/LLMAgents/` - LLM policies, adapter backends, CoSC and metrics logic.
- `CybORG/Evaluation/` - evaluation entry points and comparison runner additions.
- `cage-challenge-4/` - challenge runtime tree used in end-to-end execution.
- `results/paper_parity_matrix/` - canonical comparison outputs, traces, and summary artifacts.
- `docs/` - implementation changelog, reproducibility notes, and experiment documentation.
- `shell_scripts/` - runnable shell entrypoints (`run_cybermonics_strict.sh`, `run_cybermonics_comparison.sh`).
- `plot_scripts/` - plotting utilities (including parity/comparison plotting).

## Citation

If you use this extension, cite both the original and follow-up work:

```bibtex
@misc{castro2025largelanguagemodelsautonomous,
  title={Large Language Models are Autonomous Cyber Defenders},
  author={Sebastián R. Castro and Roberto Campbell and Nancy Lau and Octavio Villalobos and Jiaqi Duan and Alvaro A. Cardenas},
  year={2025},
  eprint={2505.04843},
  archivePrefix={arXiv},
  primaryClass={cs.AI},
  url={https://arxiv.org/abs/2505.04843}
}
```

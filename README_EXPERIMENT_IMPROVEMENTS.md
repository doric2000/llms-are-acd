# README - Experiment Improvements (Project Guide)

## 1) Document Goal

This README is dedicated to improving the original CAGE/CybORG experiment and enabling full reproducibility.
It is a single reference that explains:
- what was improved versus the original setup,
- how to run the experiment consistently,
- where all outputs are stored,
- and how to verify successful completion.

---

## 2) What Was Implemented

### Main Improvements

1. Added matrix orchestration via:
   - `CybORG/Evaluation/llamagym/run_model_comparison.py`
2. Added and improved quality metrics:
   - hallucination metrics
   - defense metrics
3. Added support for paper aliases for red variants:
   - `b_line -> aggressive`
   - `meander -> stealthy`
4. Added structured documentation and organized outputs at case and comparison levels.
5. Re-ran and repaired DeepSeek case 8 (replacing a corrupted earlier result).

---

## 3) Important Folders and What They Contain

### Execution and Evaluation Code

1. `CybORG/Evaluation/llamagym/`
   - runner and submission code for LLM experiments.
2. `cage-challenge-4/CybORG/Evaluation/llamagym/`
   - parallel copy in the challenge workspace.
3. `CybORG/Agents/LLMAgents/`
   - LLM policy, formatter, model manager, and model/prompt config files.

### Authoritative Experiment Outputs

1. `paper_parity_matrix/deepseek_steps1_7_plus_step8_20260416/`
   - canonical DeepSeek output (Steps 1-7 + replaced Step 8).
   - includes:
     - `comparison.json`
     - `comparison.md`
     - `deepseek-r1-1.5b/` with 8 cases.

2. `paper_parity_matrix/qwen_full_30x30_20260416/`
   - Qwen full-matrix run output (30x30).
   - includes:
     - `run_profile.json`
     - `qwen2.5-7b/` (case folders generated during run)

3. `paper_parity_matrix/qwen_full_30x30_20260416_run.log`
   - full live log for the Qwen run.

### Implementation Documentation

1. `IMPLEMENTATION_CHANGELOG.md`
   - chronological list of implementation changes.
2. `PHASE1_IMPLEMENTATION.md`
   - Phase 1 implementation details.

---

## 4) Current Status

1. DeepSeek:
   - canonical complete 8-case result set exists in:
     - `paper_parity_matrix/deepseek_steps1_7_plus_step8_20260416/`

2. Qwen:
   - full 30x30 run outputs are in:
     - `paper_parity_matrix/qwen_full_30x30_20260416/`
   - run log:
     - `paper_parity_matrix/qwen_full_30x30_20260416_run.log`

---

## 5) How To Run On Any Machine (No Hardcoded Paths)

Run from repository root:

```bash
REPO_ROOT="$(pwd)"
PYTHON_BIN="${REPO_ROOT}/cage-env/bin/python"
RUNNER="CybORG/Evaluation/llamagym/run_model_comparison.py"
source "${REPO_ROOT}/cage-env/bin/activate"
```

### DeepSeek Full Matrix (30x30)

```bash
"${PYTHON_BIN}" "${RUNNER}" \
  --profile quick \
  --max-eps 30 \
  --episode-length 30 \
  --matrix paper \
  --red-variants b_line,meander \
  --scenario-seeds 101,102,103,104 \
  --models deepseek-r1-1.5b \
  --output-root "${REPO_ROOT}/paper_parity_matrix/deepseek_full_30x30" \
  2>&1 | tee "${REPO_ROOT}/paper_parity_matrix/deepseek_full_30x30_run.log"
```

### Qwen Full Matrix (30x30)

```bash
"${PYTHON_BIN}" "${RUNNER}" \
  --profile quick \
  --max-eps 30 \
  --episode-length 30 \
  --matrix paper \
  --red-variants b_line,meander \
  --scenario-seeds 101,102,103,104 \
  --models qwen2.5-7b \
  --output-root "${REPO_ROOT}/paper_parity_matrix/qwen_full_30x30" \
  2>&1 | tee "${REPO_ROOT}/paper_parity_matrix/qwen_full_30x30_run.log"
```

### Single-Case Re-run (Example: Case 8)

```bash
"${PYTHON_BIN}" "${RUNNER}" \
  --profile quick \
  --max-eps 30 \
  --episode-length 30 \
  --matrix none \
  --red-variants meander \
  --scenario-seeds 104 \
  --models deepseek-r1-1.5b \
  --output-root "${REPO_ROOT}/paper_parity_matrix/step8_case8_only" \
  2>&1 | tee "${REPO_ROOT}/paper_parity_matrix/step8_case8_only_run.log"
```

---

## 6) How To Verify Correct Completion

### Minimum Checks

1. `comparison.json` and `comparison.md` exist in the output root.
2. Each of the 8 cases has `summary.json`.
3. Run log shows `return_code=0` for each case.
4. No repeated network failures in log (`ConnectionError`, `Timeout`, `HTTP 5xx`).

### Case Count Check

You must have exactly 8 matrix cases:
- aggressive: s1, s2, s3, s4
- stealthy: s1, s2, s3, s4

---

## 7) Which Files To Use For Paper Results

For final analysis and writing:
1. DeepSeek:
   - `paper_parity_matrix/deepseek_steps1_7_plus_step8_20260416/comparison.json`
2. Qwen:
   - `paper_parity_matrix/qwen_full_30x30_20260416/comparison.json` (after completion)

Per-case supporting sources:
- `summary.json`
- `scores.txt`
- `actions.txt`
- `full.txt`
- `stdout.log` / `stderr.log`

---

## 8) Operational Notes

1. Always run from the same environment (`cage-env`) to avoid dependency drift.
2. Do not mix output roots between different runs.
3. Before re-running a single case, delete only that case folder (not the entire experiment).
4. Always keep a `tee` run log for full auditability.

---

## 9) Lecturer Requirements Alignment (Sections 6-8)

This section translates the lecturer requirements into concrete writing checks for the report.

### Section 6: Critical Analysis (Strengths, Weaknesses, Limitations, Assumptions)

You must include all four categories explicitly:
1. Strengths:
   - What works well technically (for example robustness, action validity, low hallucination, stable completion).
2. Weaknesses:
   - Where performance degrades (for example specific red variant or scenario sensitivity).
3. Limitations:
   - Boundaries of your setup (limited scenarios, fixed horizon, single simulator, LLM fallback behavior).
4. Assumptions:
   - What was assumed to make claims valid (observation quality, reward fidelity, no API/network failures, representative seeds).

Evidence requirement:
- Every claim should be tied to measured output from `comparison.json` or case-level `summary.json`.
- Do not write only narrative opinions; connect each major point to at least one quantitative indicator.

Scoring intent covered:
- Supports "Depth of Critical Analysis" (7% of the 25% report component).

### Section 7: Practical Cybersecurity Impact (SOC Relevance and Feasibility)

You must address operational impact, not only model accuracy:
1. SOC relevance:
   - Map agent actions to SOC workflows (triage, containment, recovery, analyst escalation).
2. Automation boundaries:
   - Which decisions can be fully automated, and which require analyst approval.
3. Real-world feasibility:
   - Deployment constraints (latency, reliability, explainability, policy compliance, risk of false actions).
4. Safety and governance:
   - Guardrails, rollback strategy, and audit logging expectations.

Evidence requirement:
- Reference observed behavior from action logs (`actions.txt`, `full.txt`) and failure statistics.
- Include at least one concrete "deployment caveat" and one "deployment-ready use case".

Scoring intent covered:
- Supports "Technical Understanding" (8%) and "Clarity, Structure, and Academic Writing" (5%).

### Section 8: Future Research Directions

Directions must be specific and testable, not generic.

Required structure:
1. Proposed direction.
2. Why it matters (current gap it addresses).
3. How to test it (experiment design, metric, expected signal).
4. Risk/tradeoff.

Recommended minimum:
1. At least 3 concrete future directions.
2. At least 1 direction that extends implementation in this repository.
3. At least 1 direction focused on realistic SOC deployment constraints.

Scoring intent covered:
- Strengthens "Depth of Critical Analysis" and overall writing quality.

### Quick Self-Check Before Submission (Sections 6-8)

Use this pass/fail checklist:
1. Section 6 has explicit subsections: strengths, weaknesses, limitations, assumptions.
2. Section 6 claims are evidence-backed from experiment artifacts.
3. Section 7 maps findings to SOC operations and automation boundaries.
4. Section 7 includes feasibility constraints and governance/safety notes.
5. Section 8 contains at least 3 testable future directions with evaluation ideas.
6. Language is academic and precise (no unsupported broad claims).

---

## 10) Implementation Component (10%) - Submission Accuracy Checklist

To match the lecturer implementation rubric, ensure all items below are explicitly present in the submission:

Required deliverables:
1. Source code in a Git repository.
2. Short technical report (3-5 pages) with design decisions.
3. Experimental results and discussion.

Scoring alignment:
1. Correctness and technical implementation (4%):
   - Reproducible execution path and valid outputs.
2. Experimental evaluation (3%):
   - Clear setup, metrics, and result interpretation.
3. Code quality and documentation (2%):
   - Readable code, structured outputs, and clear run instructions.
4. Innovation/extension (1%):
   - Small but explicit novelty versus baseline.

Minimum evidence package recommendation:
1. `comparison.json` + `comparison.md` for each model run.
2. Case-level `summary.json` for all 8 matrix cases.
3. One combined comparison artifact (for example `final_combined_20260416/`).

---

## 11) Ready-to-Use Draft Text for Report Sections 6-8

The text below is intended as a direct draft for the academic report, aligned with lecturer requirements.

### Section 6: Critical Analysis

Our experiments reveal a clear separation between nominal completion and effective defensive quality. Both evaluated agents completed all eight benchmark cases without execution failures, indicating stable end-to-end orchestration and sufficient runtime reliability under the selected CybORG configuration. However, reliability at process level did not translate equally into defensive effectiveness.

From a strengths perspective, the Qwen-based agent demonstrated substantially better aggregate defensive outcomes. Across identical matrix settings, it achieved a mean reward of -12.6833 with low variance (standard deviation 1.8593) and a low mean hallucination rate of 0.026293. This combination suggests both behavioral consistency and stronger instruction adherence in the tested blue-team policy loop. In contrast, the DeepSeek-based agent exhibited a much lower aggregate reward (mean -3063.0042, standard deviation 1381.6669) and a materially higher mean hallucination rate (0.252589), indicating unstable policy quality and weaker robustness under scenario variation.

The main weakness is cross-scenario brittleness in the DeepSeek condition. Case-level dispersion is high, including severe negative outcomes in multiple aggressive and stealthy configurations, while one repaired case in the stealthy setting shows a near-baseline reward compared to the remaining DeepSeek distribution. This pattern indicates susceptibility to scenario-specific dynamics and potential over-reliance on fallback or suboptimal action pathways.

Several limitations constrain interpretation. First, evaluation uses a fixed matrix of two red behaviors and four scenario seeds, which is suitable for controlled comparison but limited for external generalization. Second, episode horizon and profile settings were intentionally short for reproducibility and operational throughput, potentially masking long-horizon strategic effects. Third, all conclusions are simulator-based and therefore inherit modeling assumptions of CybORG state abstraction and reward design.

The analysis also depends on explicit assumptions. We assume that logged action traces reflect actual decision behavior without hidden post-processing, that reward signals are sufficiently aligned with practical defense goals, and that no silent API degradation occurred during final successful runs. Under these assumptions, the observed gap between models is too large to be explained by minor stochastic variation alone.

### Section 7: Practical Cybersecurity Impact

For SOC relevance, the evaluated action families map naturally to core analyst workflows: Analyse supports triage and confirmation, Remove and Restore align with containment and recovery, and traffic control actions approximate policy-level isolation decisions. This makes the benchmark behavior interpretable from an operations perspective and provides a useful bridge between autonomous policy outputs and established blue-team procedures.

Operationally, the results suggest that selective automation is feasible, but full autonomy is premature. Low-risk actions such as repetitive host analysis or constrained containment can be automated with guardrails, while high-impact actions that may disrupt business services should remain analyst-gated. The large performance gap across models further implies that deployment readiness is model-dependent and cannot be inferred from framework-level success alone.

Real-world feasibility requires additional controls beyond benchmark performance. Deployment would need strict latency budgets, deterministic retry policies, explainable action rationales, and comprehensive audit logs for every control decision. In practical SOC settings, false containment or unnecessary restoration can create substantial operational cost. Therefore, policy confidence thresholds and rollback mechanisms are mandatory.

From a governance standpoint, a defensible deployment profile should include human override, explicit deny-lists for sensitive assets, and continuous drift monitoring. A realistic near-term use case is decision support with bounded automation, where the agent proposes and ranks actions while analysts retain approval authority for high-impact interventions.

### Section 8: Future Research Directions

Future work should focus on testable extensions that improve both technical performance and operational trustworthiness.

Direction 1: Confidence-calibrated action gating.
Why it matters: current outputs do not explicitly bind action execution to calibrated uncertainty.
How to test: add a confidence head or proxy score and block high-impact actions below threshold; evaluate reward change, false-action frequency, and rollback count.
Risk/tradeoff: overly conservative thresholds may reduce timely containment.

Direction 2: Hybrid policy with rule-constrained decoding.
Why it matters: hallucination-sensitive behaviors suggest benefit from hard action-space constraints.
How to test: integrate deterministic rule filters before final action emission; compare hallucination rate and mean reward against baseline runs.
Risk/tradeoff: strict rules may suppress adaptive responses in edge cases.

Direction 3: Long-horizon robustness evaluation.
Why it matters: short episodes may under-represent persistence and delayed attacker effects.
How to test: increase episode length and expand seed diversity; analyze variance growth, recovery latency, and sustained containment metrics.
Risk/tradeoff: higher compute cost and longer experimental cycles.

Direction 4: Human-in-the-loop SOC simulation.
Why it matters: practical deployment depends on analyst-agent collaboration quality.
How to test: introduce approval checkpoints for disruptive actions and measure analyst workload, decision delay, and incident resolution quality.
Risk/tradeoff: additional process overhead may offset automation gains.

Direction 5: Cross-model ensemble defense.
Why it matters: model-specific failure modes suggest potential benefit from diversified decision sources.
How to test: implement ensemble voting or arbitration between two policy generators; evaluate whether tail-risk cases are reduced.
Risk/tradeoff: increased system complexity and debugging burden.

These directions are measurable within the current repository structure and can be implemented as incremental extensions to the existing comparison runner and case-level logging pipeline.

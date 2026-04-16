# Seed Analysis for Paper Parity

## Current Situation

**Our script** (`run_cybermonics_strict.sh`):
- Does NOT pass a `--seed` parameter to evaluation
- Result: **Random seed each run** (non-deterministic)

**Paper** (Castro et al., arXiv:2505.04843v2):
- Does NOT explicitly mention a seed value in the text
- Does NOT mention random seed or reproducibility constraints
- Likely uses default CybORG behavior (which is random seed if not specified)

## What This Means

- ✅ Our setup matches paper (both use no fixed seed mentioned)
- ⚠️ Results will vary slightly between runs (randomness in environment)
- ✅ This is **NOT a problem for comparison** (paper also has this randomness)

## Available Scenarios

The paper tested against:
- **Primary**: FiniteState red agent (Fig. 4)
- **Additional**: AggressiveFSM, StealthyFSM, ImpactFSM, DegradeServiceFSM (Fig. 5)

Our script uses:
- Default: `CAGE4_RED_AGENT_VARIANT=finite_state` ✅ **Matches Fig. 4**

## If You Want Fixed Seed

For reproducibility, you can add `--seed <value>` parameter:

```bash
# With seed=12345 for reproducibility
source /home/dor/llms-are-acd/cage-env/bin/activate && \
cd /home/dor/llms-are-acd/cage-challenge-4 && \
export CAGE4_ENFORCE_STRICT_BASELINE=true && \
export CAGE4_BASELINE_MAX_EPS=2 && \
export CAGE4_BASELINE_EPISODE_LENGTH=500 && \
python -m CybORG.Evaluation.evaluation \
  --max-eps 2 \
  --seed 12345 \
  CybORG/Evaluation/Cybermonics \
  /home/dor/llms-are-acd/cybermonics_strict_comparison_deepseek/results
```

## Recommendation

**Keep as is** - The paper doesn't specify a fixed seed, so:
- Running multiple times shows variability (like paper might have)
- Gives you confidence in the results (different seeds, consistent outcome)
- Matches paper's apparent approach

If you want deterministic results for validation, add `--seed 101` (first scenario seed used in matrix runs).

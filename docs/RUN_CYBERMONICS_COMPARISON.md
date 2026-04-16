# Running Cybermonics with 1 LLM + 4 KEEP GNN Agents (2 Episodes × 500 Steps)

## Commands

### Using DeepSeek-r1-1.5b (Default)
```bash
bash shell_scripts/run_cybermonics_strict.sh
```
or explicitly:
```bash
bash shell_scripts/run_cybermonics_strict.sh deepseek
```

### Using Qwen2.5-7b
```bash
bash shell_scripts/run_cybermonics_strict.sh qwen
```

### Manual Full Command (DeepSeek)

Run this from the repository root:

```bash
#!/bin/bash
source ./cage-env/bin/activate

cd ./cage-challenge-4

# Set strict profile to match paper: 2 episodes × 500 steps each (1000 total steps)
export CAGE4_ENFORCE_STRICT_BASELINE=true
export CAGE4_BASELINE_MAX_EPS=2
export CAGE4_BASELINE_EPISODE_LENGTH=500

# Red agent: FiniteState (default, matches paper Fig. 4)
export CAGE4_RED_AGENT_VARIANT=finite_state

# LLM Model: DeepSeek
export CAGE4_MODEL_CONFIG="config/model/ollama-deepseek-r1-8b.yml"

# Run evaluation with Cybermonics submission  
# (has 1 LLM blue_agent_4 + 4 KEEP GNN agents blue_agent_0-3)
mkdir -p ./results/cybermonics_strict_comparison_deepseek
python -m CybORG.Evaluation.evaluation \
  --max-eps 2 \
  CybORG/Evaluation/Cybermonics \
  ./results/cybermonics_strict_comparison_deepseek/results
```

### Manual Full Command (Qwen)

```bash
#!/bin/bash
source ./cage-env/bin/activate

cd ./cage-challenge-4

# Set strict profile to match paper: 2 episodes × 500 steps each (1000 total steps)
export CAGE4_ENFORCE_STRICT_BASELINE=true
export CAGE4_BASELINE_MAX_EPS=2
export CAGE4_BASELINE_EPISODE_LENGTH=500

# Red agent: FiniteState (default, matches paper Fig. 4)
export CAGE4_RED_AGENT_VARIANT=finite_state

# LLM Model: Qwen
export CAGE4_MODEL_CONFIG="config/model/qwen2.5-7b.yml"

# Run evaluation with Cybermonics submission  
mkdir -p ./results/cybermonics_strict_comparison_qwen
python -m CybORG.Evaluation.evaluation \
  --max-eps 2 \
  CybORG/Evaluation/Cybermonics \
  ./results/cybermonics_strict_comparison_qwen/results
```

## Configuration Match with Paper

| Configuration | Paper | Local (Cybermonics) |
|---|---|---|
| **Episodes** | 2 | ✅ 2 |
| **Steps/Episode** | 500 | ✅ 500 |
| **Total Steps** | 1000 | ✅ 1000 |
| **Red Agent** | FiniteState | ✅ FiniteState |
| **Blue Agent 4 (LLM)** | Multiple models (o3-mini, o1-mini, gpt-4o-mini, DeepSeek-V3) | DeepSeek-r1-1.5b (local) |
| **Blue Agents 0-3 (RL)** | KEEP GNN PPO | ✅ KEEP GNN PPO |

## Key Difference

- **LLM Model**: Paper tested o-series OpenAI + DeepSeek-V3
- **Local**: Using DeepSeek-r1-1.5b (Ollama)
- **Impact**: Directional comparison only, not apples-to-apples due to different LLM

## What Gets Run

The Cybermonics submission in `CybORG/Evaluation/Cybermonics/submission.py` automatically:

1. Loads pre-trained KEEP GNN agents from `weights/gnn_ppo-0.pt` ... `weights/gnn_ppo-4.pt`
2. Replaces only `blue_agent_4` with `DefenderAgent` (LLM)
3. Keeps `blue_agent_0-3` as trained KEEP GNN agents
4. Uses CombinedWrapper to route observations correctly

This matches the paper's 1 LLM + 4 RL baseline exactly.

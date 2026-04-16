# FRESH START: Cybermonics 1 LLM + 4 KEEP GNN Comparison

## Overview

This guide explains how to properly compare the paper's results with local runs using **Cybermonics submission** (which has the correct KEEP GNN RL agents).

## Critical Issue with Previous Runs

You were using **llamagym submission** which has:
- ❌ `ReactRemoveBlueAgent` (simple heuristic) for agents 0-3
- ✅ `DefenderAgent` (LLM) for agent 4

The **paper used**:
- ✅ Cybermonic's KEEP GNN PPO (trained) for agents 0-3
- ✅ LLM agent for agent 4

**These are NOT comparable.** You need to use **Cybermonics submission** instead.

---

## Solution: Use Cybermonics Submission

**Location**: `/home/dor/llms-are-acd/cage-challenge-4/CybORG/Evaluation/Cybermonics/`

**What it has**:
```python
# Loads pre-trained KEEP GNN weights automatically
AGENTS = {
    f"blue_agent_{i}": load(f'weights/gnn_ppo-{i}.pt')
    for i in range(5)
}

# Replaces only blue_agent_4 with LLM
AGENTS["blue_agent_4"] = DefenderAgent("blue_agent_4", LLMDefenderPolicy, [])
```

**Pre-trained weights**: ✅ Available at `weights/gnn_ppo-0.pt` ... `weights/gnn_ppo-4.pt`

---

## Running the Comparison

### Option A: Use the Script (Recommended)

#### Default (DeepSeek-r1-1.5b)
```bash
bash /home/dor/llms-are-acd/run_cybermonics_strict.sh
```

#### With Qwen2.5-7b
```bash
bash /home/dor/llms-are-acd/run_cybermonics_strict.sh qwen
```

### Option B: Manual Command

```bash
# Activate environment
source /home/dor/llms-are-acd/cage-env/bin/activate

# Navigate to CAGE 4
cd /home/dor/llms-are-acd/cage-challenge-4

# Set strict baseline (paper-parity)
export CAGE4_ENFORCE_STRICT_BASELINE=true
export CAGE4_BASELINE_MAX_EPS=2
export CAGE4_BASELINE_EPISODE_LENGTH=500
export CAGE4_RED_AGENT_VARIANT=finite_state

# Run evaluation
python -m CybORG.Evaluation.evaluation \
  --max-eps 2 \
  CybORG/Evaluation/Cybermonics \
  /home/dor/llms-are-acd/cybermonics_strict_comparison/results
```

---

## Configuration Details

### Strict Baseline (Paper-Parity) ✅

| Parameter | Value | Note |
|---|---|---|
| **Episodes** | 2 | Paper = 2 |
| **Steps per episode** | 500 | Paper = 500 |
| **Total steps** | **1000** (not 900) | 2 × 500 = 1000 |
| **Red agent** | FiniteState | Paper Fig. 4 uses default |
| **Blue agents 0-3** | KEEP GNN PPO | ✅ Paper baseline |
| **Blue agent 4** | LLM | ✅ Paper setup |

### Progress Bar

The progress bar will dynamically show **1000 steps** when running with strict baseline.

**How it works**:
- Environment variables `CAGE4_BASELINE_MAX_EPS` and `CAGE4_BASELINE_EPISODE_LENGTH` are read
- Progress bar total = max_eps × episode_length
- 2 × 500 = 1000 steps (not 900)
- The function `_get_progress_bar_total()` in `config_vars.py` handles this automatically

---

## What's Different from Paper

**LLM Model**:
- Paper tested: o3-mini, o1-mini, gpt-4o-mini, **DeepSeek-V3**
- Local: **DeepSeek-r1-1.5b** (Ollama)

**Impact**: 
- Directional comparison only (shows relative performance)
- Not apples-to-apples comparison due to different LLM model
- But RL baseline (KEEP GNN) will be **exactly** the same

---

## Expected Output

After running, you'll get:
- `comparison.json` - Metrics in JSON format
- `comparison.md` - Human-readable summary
- `results.txt` - Raw output
- And other diagnostic files

Extract reward and runtime from these files for comparison with paper's Fig. 4 and Fig. 5.

---

## Files Changed

✅ `/home/dor/llms-are-acd/README.md` - Added Cybermonics explanation  
✅ `/home/dor/llms-are-acd/cage-challenge-4/CybORG/Agents/LLMAgents/config/config_vars.py` - Made progress bar dynamic  
✅ `/home/dor/llms-are-acd/CybORG/Agents/LLMAgents/config/config_vars.py` - Made progress bar dynamic  
✅ `/home/dor/llms-are-acd/run_cybermonics_strict.sh` - Created execution script  
✅ `/home/dor/llms-are-acd/RUN_CYBERMONICS_COMPARISON.md` - Created documentation  

---

## Next Steps

1. ✅ Run the script: `bash run_cybermonics_strict.sh` (DeepSeek) or `bash run_cybermonics_strict.sh qwen` (Qwen)
2. Extract results for comparison
3. Create figures comparing with paper's Fig. 4 and Fig. 5
4. Document caveats about LLM model difference

All configuration is now correctly set up for **1000 steps** (2 episodes × 500 steps).

---

## Available LLM Models

Both models are configured for Ollama backend at `http://10.100.102.201:11435/v1`:

| Model | Config File | Model Name | Backend | Context | Max Tokens |
|---|---|---|---|---|---|
| **DeepSeek-r1-1.5b** | `ollama-deepseek-r1-8b.yml` | `deepseek-r1:1.5b` | Ollama | - | 384 |
| **Qwen2.5-7b** | `qwen2.5-7b.yml` | `qwen2.5:7b` | Ollama | 4096 | - |

**Note**: Both are Ollama local models (not cloud-based). Ensure Ollama server is running at the configured URL.

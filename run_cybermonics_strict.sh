#!/bin/bash

################################################################################
# RUN_CYBERMONICS_STRICT.sh
# 
# Runs Cybermonics submission with proper 1 LLM + 4 KEEP GNN configuration
# Configuration: 2 episodes × 500 steps = 1000 total steps (matches paper)
# Red Agent: FiniteStateRedAgent (default, matches paper Fig. 4)
# Blue Agent 4: LLM (DefenderAgent) with selectable Ollama model
# Blue Agents 0-3: KEEP GNN PPO (pre-trained, matches paper)
#
# Usage: 
#   bash run_cybermonics_strict.sh [model] [seed]
#
# Examples:
#   bash run_cybermonics_strict.sh                    # deepseek, random seed (matches paper)
#   bash run_cybermonics_strict.sh deepseek           # deepseek, random seed
#   bash run_cybermonics_strict.sh qwen               # qwen, random seed
#   bash run_cybermonics_strict.sh deepseek 101       # deepseek, fixed seed=101
#   bash run_cybermonics_strict.sh qwen 42            # qwen, fixed seed=42
#
# Note: Paper doesn't specify a seed, so random seed (no --seed) matches paper behavior.
#       Add seed parameter for reproducible results.
################################################################################

set -e  # Exit on error

# Parse model argument (default: deepseek)
MODEL="${1:-deepseek}"

# Parse seed argument (default: empty, which means random seed like paper)
SEED="${2:-}"

# Map model names to config paths
case "$MODEL" in
  deepseek)
    MODEL_NAME="DeepSeek-r1-1.5b"
    MODEL_CONFIG="ollama-deepseek-r1-8b.yml"
    OUTPUT_SUFFIX="deepseek"
    ;;
  qwen)
    MODEL_NAME="Qwen2.5-7b"
    MODEL_CONFIG="qwen2.5-7b.yml"
    OUTPUT_SUFFIX="qwen"
    ;;
  *)
    echo "❌ Unknown model: $MODEL"
    echo "Supported models: deepseek, qwen"
    exit 1
    ;;
esac

# Build seed string for output
if [ -z "$SEED" ]; then
  SEED_STR="(random, like paper)"
  SEED_ARG=""
else
  SEED_STR="$SEED"
  SEED_ARG="--seed $SEED"
fi

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║   CYBERMONICS 1 LLM + 4 KEEP GNN STRICT COMPARISON            ║"
echo "║   LLM Model: $MODEL_NAME"
echo "║   Seed: $SEED_STR"
echo "║   (2 episodes × 500 steps = 1000 total steps)                  ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Activate environment
echo "[1/5] Activating environment..."
source /home/dor/llms-are-acd/cage-env/bin/activate

# Set directory
cd /home/dor/llms-are-acd/cage-challenge-4
echo "[2/5] Working directory: $(pwd)"
echo ""

# Configure strict baseline (paper-parity)
echo "[3/5] Setting strict baseline configuration:"
export CAGE4_ENFORCE_STRICT_BASELINE=true
export CAGE4_BASELINE_MAX_EPS=2
export CAGE4_BASELINE_EPISODE_LENGTH=500
export CAGE4_MODEL_CONFIG="CybORG/Agents/LLMAgents/config/model/$MODEL_CONFIG"
echo "      - Episodes: 2"
echo "      - Steps per episode: 500"
echo "      - Total steps: 1000 (not 900)"
echo "      - Red agent: FiniteState"
echo "      - LLM model: $MODEL_NAME ($MODEL_CONFIG)"
echo "      - Temperature: 1.0 (paper-compliant)"
echo ""

# Create output directory
OUTPUT_DIR="/home/dor/llms-are-acd/cybermonics_strict_comparison_${OUTPUT_SUFFIX}"
if [ -n "$SEED" ]; then
  OUTPUT_DIR="${OUTPUT_DIR}_seed${SEED}"
fi
mkdir -p "$OUTPUT_DIR"

# Capture the full console transcript for reproducibility.
RUN_LOG="$OUTPUT_DIR/run.log"
exec > >(tee "$RUN_LOG") 2>&1

echo "[4/5] Model configuration (temperature verification):"
cat "CybORG/Agents/LLMAgents/config/model/$MODEL_CONFIG" | grep -A 5 "^generate:"
echo ""

echo "[5/5] Running evaluation..."
echo "      Output: $OUTPUT_DIR/results"
echo ""

# Run evaluation with Cybermonics submission
# Note: Paper does not specify a seed, so no --seed argument mirrors paper behavior
python -m CybORG.Evaluation.evaluation \
  --max-eps 2 \
  $SEED_ARG \
  CybORG/Evaluation/Cybermonics \
  "$OUTPUT_DIR/results"

echo ""
echo "✅ Evaluation complete!"
echo "Results saved to: $OUTPUT_DIR"
echo "Console log saved to: $RUN_LOG"
echo ""
echo "Files generated:"
ls -lh "$OUTPUT_DIR/" | tail -n +2 | awk '{print "  - " $9 " (" $5 ")"}'

#!/bin/bash
# Run proper 1 LLM + 4 KEEP GNN comparison

echo "Starting Cybermonics submission evaluation..."
echo "Configuration: 1 DeepSeek LLM + 4 KEEP GNN agents vs FiniteState red agent"
echo "Profile: 2 episodes × 500 steps per episode"
echo ""

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT/cage-challenge-4"

# Activate environment
source "$REPO_ROOT/cage-env/bin/activate"

# Set strict baseline enforcement
export CAGE4_ENFORCE_STRICT_BASELINE=true
export CAGE4_BASELINE_MAX_EPS=2
export CAGE4_BASELINE_EPISODE_LENGTH=500

# Set red agent variant (default is finite_state which matches paper)
export CAGE4_RED_AGENT_VARIANT=finite_state

# Set LLM configuration (use DeepSeek)
export CAGE4_MODEL_CONFIG=config/model/ollama-deepseek-r1-1.5b.yml

# Create output directory
OUTPUT_DIR="$REPO_ROOT/results/paper_comparison_deepseek_keep_strict"
mkdir -p "$OUTPUT_DIR"

echo "Output directory: $OUTPUT_DIR"
echo ""

# Run evaluation with Cybermonics submission (which has 1 LLM + 4 KEEP GNN)
python -m CybORG.Evaluation.evaluation \
  --max-eps 2 \
  CybORG/Evaluation/Cybermonics \
  "$OUTPUT_DIR/results"

echo ""
echo "Evaluation complete!"
echo "Results saved to: $OUTPUT_DIR"
ls -la "$OUTPUT_DIR/"

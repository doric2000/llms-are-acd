# Quick Reference: Run Comparison with Different Models

## Default Commands (Random Seed - Matches Paper)

**DeepSeek-r1-1.5b** (default):
```bash
bash /home/dor/llms-are-acd/run_cybermonics_strict.sh
```

**Qwen2.5-7b**:
```bash
bash /home/dor/llms-are-acd/run_cybermonics_strict.sh qwen
```

## With Fixed Seed (For Reproducibility)

**DeepSeek with seed=101**:
```bash
bash /home/dor/llms-are-acd/run_cybermonics_strict.sh deepseek 101
```

**Qwen with seed=42**:
```bash
bash /home/dor/llms-are-acd/run_cybermonics_strict.sh qwen 42
```

## Output Directories

- DeepSeek (random): `cybermonics_strict_comparison_deepseek/results`
- DeepSeek (seed=101): `cybermonics_strict_comparison_deepseek_seed101/results`
- Qwen (random): `cybermonics_strict_comparison_qwen/results`
- Qwen (seed=42): `cybermonics_strict_comparison_qwen_seed42/results`

---

## Configuration

All runs use:
- **Episodes**: 2
- **Steps per episode**: 500
- **Total steps**: 1000
- **Red agent**: FiniteState (matches paper Fig. 4)
- **Blue agents 0-3**: KEEP GNN PPO (pre-trained, matches paper)
- **Blue agent 4**: LLM (either DeepSeek or Qwen)

---

## Comparison Cells

After running, the metrics are typically in:
- `results.txt` - Full output
- `comparison.json` - Metrics in JSON
- `comparison.md` - Structured summary

Extract:
- **Reward**: Final cumulative reward
- **Runtime**: Total execution time
- **Episode lengths**: Steps actually taken

---

## Model Details

### DeepSeek-r1-1.5b
- Backend: Ollama
- URL: `http://10.100.102.201:11435/v1`
- Model: `deepseek-r1:1.5b`
- Max tokens: 384
- Temperature: 1.0

### Qwen2.5-7b  
- Backend: Ollama
- URL: `http://10.100.102.201:11435/v1`
- Model: `qwen2.5:7b`
- Context: 4096 tokens
- Temperature: 1.0

---

## To Compare Results

Run both models and compare:

```bash
# DeepSeek
bash /home/dor/llms-are-acd/run_cybermonics_strict.sh deepseek

# Qwen
bash /home/dor/llms-are-acd/run_cybermonics_strict.sh qwen

# Then compare outputs from:
# /home/dor/llms-are-acd/cybermonics_strict_comparison_deepseek/results
# /home/dor/llms-are-acd/cybermonics_strict_comparison_qwen/results
```

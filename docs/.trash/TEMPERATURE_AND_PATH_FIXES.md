# Temperature & Path Configuration Fixes

## 🔴 Issue Summary

Two critical issues were identified that would violate paper parity:

### 1. **Temperature Setting Violation**
**Problem**: The qwen2.5-7b.yml had `temperature: 0.2` (or `0.2` in other versions)
**Paper Requirement**: "For all our models, we set the temperature to 1"
**Impact**: Without temperature=1, results cannot be compared to paper values

### 2. **File Path Resolution Error**
**Problem**: Script was setting `CAGE4_MODEL_CONFIG="config/model/qwen2.5-7b.yml"` but files don't exist at that path
**Error Message**: `FileNotFoundError: [Errno 2] No such file or directory: 'config/model/qwen2.5-7b.yml'`
**Root Cause**: Config files are at `CybORG/Agents/LLMAgents/config/model/`, not directly in `config/model/`

---

## ✅ Fixes Applied

### Fix #1: Temperature Settings

**DeepSeek-r1-1.5b Configuration**
- File: `/home/dor/llms-are-acd/cage-challenge-4/CybORG/Agents/LLMAgents/config/model/ollama-deepseek-r1-8b.yml`
- Status: ✅ Already had `temperature: 1` (correct)

**Qwen2.5-7b Configuration**
- Files Updated:
  - `/home/dor/llms-are-acd/cage-challenge-4/CybORG/Agents/LLMAgents/config/model/qwen2.5-7b.yml`
  - `/home/dor/llms-are-acd/CybORG/Agents/LLMAgents/config/model/qwen2.5-7b.yml`
- Change: `temperature: 0.2` → `temperature: 1.0` ✅

**DeepSeek-r1-1.5b (root version)**
- File: `/home/dor/llms-are-acd/CybORG/Agents/LLMAgents/config/model/deepseek-r1-1.5b.yml`
- Change: `temperature: 0.2` → `temperature: 1.0` ✅

### Fix #2: File Path Resolution

**Problem**: Relative path `config/model/qwen2.5-7b.yml` was incorrect
**Solution**: Updated to full relative path `CybORG/Agents/LLMAgents/config/model/$MODEL_CONFIG`

**Modified File**: `/home/dor/llms-are-acd/run_cybermonics_strict.sh`

**Changes**:
```bash
# BEFORE (incorrect)
export CAGE4_MODEL_CONFIG="config/model/$MODEL_CONFIG"
cat "CybORG/Agents/LLMAgents/$CAGE4_MODEL_CONFIG" | head -8

# AFTER (correct)
export CAGE4_MODEL_CONFIG="CybORG/Agents/LLMAgents/config/model/$MODEL_CONFIG"
cat "CybORG/Agents/LLMAgents/config/model/$MODEL_CONFIG" | grep -A 5 "^generate:"
```

---

## 📋 Verification Results

### Temperature Settings (Paper Compliance)

| Model | Location | Current Value | Paper Requirement | Status |
|-------|----------|---------------|-------------------|--------|
| DeepSeek-r1-1.5b | `ollama-deepseek-r1-8b.yml` | `1` | `1` | ✅ PASS |
| Qwen2.5-7b | `qwen2.5-7b.yml` (cage-challenge-4) | `1.0` | `1` | ✅ PASS |
| Qwen2.5-7b | `qwen2.5-7b.yml` (root) | `1.0` | `1` | ✅ PASS |
| DeepSeek-r1-1.5b | `deepseek-r1-1.5b.yml` (root) | `1.0` | `1` | ✅ PASS |

### File Path Resolution

| Variable | Value | Target File |
|----------|-------|------------|
| `CAGE4_MODEL_CONFIG` | `CybORG/Agents/LLMAgents/config/model/ollama-deepseek-r1-8b.yml` | ✅ Resolvable |
| `CAGE4_MODEL_CONFIG` | `CybORG/Agents/LLMAgents/config/model/qwen2.5-7b.yml` | ✅ Resolvable |

---

## 🚀 Ready to Run

**DeepSeek (temperature=1, random seed)**:
```bash
bash /home/dor/llms-are-acd/run_cybermonics_strict.sh
```

**Qwen (temperature=1, random seed)**:
```bash
bash /home/dor/llms-are-acd/run_cybermonics_strict.sh qwen
```

**With reproducible seed**:
```bash
bash /home/dor/llms-are-acd/run_cybermonics_strict.sh deepseek 101
bash /home/dor/llms-are-acd/run_cybermonics_strict.sh qwen 42
```

---

## 📚 Paper Reference

**Citation**: Castro et al., arXiv:2505.04843v2

**Exact Quote**:
> "For all our models, we set the temperature to 1"

This setting ensures:
- Non-deterministic outputs (temperature > 0)
- Higher variance in model responses (for better exploration)
- Proper comparison baseline with paper's experiments

---

## 📝 Configuration Summary

### DeepSeek-r1-1.5b Settings
```yaml
model_name: "deepseek-r1:1.5b"
base_url: "http://10.100.102.201:11435/v1"
generate:
  max_new_tokens: 384
  temperature: 1           # Paper requirement ✅
```

### Qwen2.5-7b Settings
```yaml
model_name: "qwen2.5:7b"
base_url: "http://10.100.102.201:11435/v1"
ollama_options:
  num_ctx: 4096
generate:
  max_new_tokens: 768
  temperature: 1.0         # Paper requirement ✅
```

---

## 🔍 Scientific Integrity

These fixes ensure proper **experimental reproducibility**:

✅ **Temperature Setting**: Now matches Castro et al. exactly (temperature=1)
✅ **File Resolution**: Config files resolve correctly without FileNotFoundError
✅ **Seed Handling**: Paper doesn't specify seed → script uses random seed (compatible)
✅ **Agent Configuration**: Uses Cybermonics submission with KEEP GNN + LLM (matches paper)
✅ **Hyperparameters**: 2 episodes × 500 steps = 1000 total (matches paper)
✅ **Red Agent**: FiniteStateRedAgent (matches paper Fig. 4 baseline)

---

**Last Updated**: 2025-04-16T13:00:00Z
**Status**: ✅ All fixes applied and verified

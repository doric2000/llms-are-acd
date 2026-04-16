# Phase 1: Immediate Problem Fixes

## Objective
Improve model output quality and reduce fallback-to-Sleep rate without changing core evaluation logic.

## Changes Implemented

### 1. Reduced Prompt Verbosity ✅
**File**: `prompt.yml`

**What changed**:
- Action descriptions: Reduced from 200+ words to 20-30 word summaries
  - Kept essential info: what action does, when to use it
  - Removed: extensive context about consequences and technical details
- Environment rules section: Simplified from detailed breakdown to key conceptual rules
  - Removed redundant mission-phase details
  - Consolidated network structure into "4 Networks: Deployed A/B, HQ, Contractor"
  - Kept critical defense setup (5 defenders, undefended contractor network)
- CommVector section: Kept intact (agents understand binary format)

**Rationale**: Shorter context allows models to focus on reasoning instead of parsing verbose rules. Ollama models with limited context (4096 tokens) benefit from concise guidance.

**Metric target**: Reduce prompt token usage by ~20% (342 → ~280 tokens for system prompt)

---

### 2. Increased Repair Attempts ✅
**Files**: Model configs
- `deepseek-r1-1.5b.yml`: Already at 3 repair attempts (no change needed)
- `qwen2.5-7b.yml`: Already at 3 repair attempts (from creation)

**Status**: Both competitive models have `repair_attempts: 3`
- Allows up to 3 structured-output recovery attempts before fallback
- Repair loop triggered when JSON parsing fails
- Each attempt gets stronger guidance ("STRICT JSON", "exactly two keys", etc.)

---

### 3. Intelligent Fallback Action Pool ✅
**File**: `CybORG/Agents/LLMAgents/llm_adapter/model_manager.py`

**New method**: `_infer_fallback_action(raw_response)`

**Fallback strategy**:
1. Try to extract any hostname from raw response text
2. If hostname found → `Analyse host:HOSTNAME` (gather intelligence, free action)
3. If no hostname → `Sleep` (safest default)

**Rationale**: 
- Instead of immediately going to Sleep on parse failure, try to salvage the response
- Analyse is ideal fallback: costs action slot but doesn't risk availability issues
- Better than Sleep because it actually tries to defend (gathers intel first)
- Still safe: no risk of incorrect host targets or subnet blocks

**Call chain**:
```
generate_structured_response()
  ├─ parse from JSON (tries 3 repair attempts)
  ├─ if all fail: _infer_fallback_action()  ← NEW
  └─ if still fails: Sleep
```

---

### 4. Generation Parameter Tuning ✅
**Files**: Model configs

**DeepSeek adjustments**:
- `max_new_tokens`: 1024 → 512 (was wasteful, most responses <200 tokens)
- `repair_attempts`: Already 3
- `temperature`: 0.2 (good balance: not too random, not too repetitive)

**Qwen adjustments** (from creation):
- `max_new_tokens`: 768 (moderate, flexible for longer reasoning)
- `temperature`: 0.2 (matches DeepSeek)
- `request_timeout_sec`: 120s (Qwen is typically slower; needs breathing room)

---

## Expected Outcomes

| Before Phase 1 | After Phase 1 |
|---|---|
| ~8-15% invalid actions | ~3-5% invalid actions (via fallback) |
| Immediate Sleep fallback | Analyse-first fallback |
| Prompt: ~364 tokens | Prompt: ~280 tokens |
| Repair attempts: 3 (DeepSeek), 3 (Qwen) | Repair attempts: 3 (both) |
| Fallback: Sleep only | Fallback: Analyse → Sleep |

---

## Testing Protocol

Run comparison with Phase 1 enabled:
```bash
cd /home/dor/llms-are-acd
source cage-env/bin/activate
python CybORG/Evaluation/llamagym/run_model_comparison.py \
  --quick \
  --episode-length 2 \
  --heartbeat-sec 5 \
  --timeout-sec 360 \
  --wandb-mode offline \
  --models deepseek-r1-1.5b,qwen2.5-7b
```

Check output logs:
- `[ASSISTANT]` responses should show valid actions (Remove, Analyse, BlockTrafficZone, etc.)
- Fallback messages should show `Analyse host:...` instead of immediate Sleep
- No markdown-formatted weak values like `"** None."` or `"** Sleep."`

---

## What's NOT Fixed (Out of Scope for Phase 1)

1. **Reward system** (CybORG design limitation):
   - BlueRewardMachine is penalty-only; Blue doesn't earn points for good defense
   - Valid actions still yield negative/zero reward (action cost - impact prevention)
   - This is expected; Phase 1 focuses on action *quality*, not reward magnitude

2. **Preventative CoSC** (Chain-of-Self-Correction):
   - Current: Repair-after-failure (post-hoc JSON fixing)
   - Paper intent: Verify-before-action (preventative contradiction detection)
   - Deferred to Phase 2 (requires more complex prompting)

3. **Systematic evaluation protocol**:
   - Current: --quick mode (2 eps × 2 steps)
   - Paper target: Full sweep (2 eps × 4 red agents × 2 models)
   - Created `--models` CLI option to support this; full protocol in Phase 3

4. **Reasoning analysis**:
   - Deferred to Phase 4 (clustering, embeddings, analysis)

---

## Next Steps

After Phase 1 validation (confirm action quality ↑):
→ **Phase 2: Preventative CoSC** (2-3 days)
   - Add verification section to prompt
   - Detect contradictions (e.g., Restore on clean host)
   - Track verification success rates

→ **Phase 3: Full Evaluation Protocol** (1-2 days)
   - 4 red agents × 2 models × 2 episodes
   - Comprehensive metrics table (µ, σ, MTTR)

→ **Phase 4: Reasoning Analysis** (1 day)
   - Cluster action-reason pairs
   - Compare to RL baseline strategies

# Cybermonic RL Agent Guide

This page explains how the Cybermonic RL agents are built, how they are trained, and how to use/extend them for future work.

## 1) What These Agents Are

Cybermonic defenders are **graph-based PPO agents** trained in CybORG CAGE-4.

- Primary training entrypoint: `cybermonic_train.py`
- Agent implementation: `CybORG/Agents/CybermonicAgents/cage4.py`
- Memory buffer: `CybORG/Agents/CybermonicAgents/memory_buffer.py`
- Observation wrapper: `CybORG/Agents/Wrappers/CybermonicWrappers/graph_wrapper.py`

The training pipeline builds **5 RL blue agents** (`N_AGENTS = 5`) and trains them in the enterprise scenario.

## 2) Core Algorithm

The agent class `InductiveGraphPPOAgent` uses:

- **PPO (Proximal Policy Optimization)** for policy updates
- **Graph neural network (GCNConv)** encoders for actor and critic
- **Clipped ratio objective** in PPO (`clip` hyperparameter)
- **Entropy regularization** to maintain exploration
- **Critic MSE loss** for value regression

Loss structure in training update (`learn()`):

- `actor_loss = -mean(min(r_theta * A, clipped_r_theta * A))`
- `critic_loss = MSE(return, value)`
- `total_loss = actor_loss + 0.5 * critic_loss - 0.01 * entropy`

## 3) Model Architecture (Build Details)

### Actor (`InductiveActorNetwork`)

- Two GCN layers:
  - `GCNConv(in_dim -> hidden1)`
  - `GCNConv(hidden1 -> hidden2)`
- Three self-attention passes (`SimpleSelfAttention`) to build global context
- Action heads:
  - node-action head
  - edge-action head
  - global-action head (e.g., sleep-like global action)
- Final action distribution:
  - `Categorical(softmax(logits))`

### Critic (`InductiveCriticNetwork`)

- Two GCN layers
- Self-attention global aggregation
- Value head outputs scalar state value

## 4) Exact Training Hyperparameters (Default)

Defined in `cybermonic_train.py`:

### Run-level defaults

- `SEED = 1337`
- `N = 25` episodes collected before each update cycle
- `workers = 25` parallel episode generators
- `bs = 2500` PPO minibatch split size
- `episode_len = 500`
- `training_episodes = 50_000`
- `epochs = 4` PPO epochs per update
- `N_AGENTS = 5`
- `MAX_THREADS = 36`

### PPO-level defaults (agent class)

From `InductiveGraphPPOAgent(...)` constructor and training script:

- `gamma = 0.99`
- `lambda = 0.95`
- `clip = 0.2` (explicitly passed from training script)
- `epochs = 4`
- actor learning rate: `0.0003`
- critic learning rate: `0.001`
- actor hidden dims from CLI:
  - `--hidden` default `256`
  - `--embedding` default `128`

## 5) Environment and Scenario Used During Training

Training uses CAGE-4 enterprise simulation:

- Blue shell class during generation: `SleepAgent` (actual decisions come from trained RL policy via wrapper state/action flow)
- Green agent: `EnterpriseGreenAgent`
- Red agent: `FiniteStateRedAgent`
- Scenario generator: `EnterpriseScenarioGenerator`
- Environment wrapper: `GraphWrapper`

## 6) How Training Loop Works

1. Build 5 `InductiveGraphPPOAgent` instances.
2. Spawn parallel env workers (`joblib` processes).
3. Generate episodes and collect per-agent PPO memories.
4. Merge memories across episodes.
5. Run PPO updates in parallel across agents (`joblib` threads).
6. Log reward/loss to `wandb`.
7. Save checkpoints to `checkpoints/` and training logs to `logs/`.

Checkpoint behavior:

- Always writes rolling checkpoint:
  - `checkpoints/{fname}-{agent_idx}_checkpoint.pt`
- Periodic snapshot approximately every 10k episodes:
  - `checkpoints/{fname}-{agent_idx}_{k}k.pt`

## 7) How To Train

From repository root:

```bash
source env-cage/bin/activate
source .env
```

Basic training:

```bash
python cybermonic_train.py my_agent
```

Custom architecture:

```bash
python cybermonic_train.py my_agent --hidden 512 --embedding 256
```

With online wandb logging:

```bash
python cybermonic_train.py my_agent \
  --wandb-mode online \
  --wandb-entity <your_entity> \
  --experiment-name cybermonic_train_run
```

Outputs:

- Checkpoints: `checkpoints/`
- Logs: `logs/`

## 8) How To Use Trained Agents

Typical use pattern:

1. Train with `cybermonic_train.py`.
2. Keep checkpoint files from `checkpoints/`.
3. Load checkpoints in evaluation/submission path that expects KEEP/Cybermonic-style RL weights.

In this repository, Cybermonics evaluation uses pretrained RL weight files under:

- `CybORG/Evaluation/Cybermonics/weights/`

For custom future runs, replace or version these weights with your trained checkpoints and keep naming/layout consistent with evaluation loader expectations.

## 9) Future Work: Practical Extension Ideas

### A) Algorithmic improvements

- PPO schedule tuning (clip decay, LR decay, entropy schedule)
- GNN architecture swap (GraphSAGE/GAT)
- Advantage normalization variants and GAE tuning

### B) Training protocol improvements

- Red-agent curriculum (FiniteState -> aggressive/stealthy/etc.)
- Longer horizon experiments and seed sweeps
- Better checkpoint selection policy (best-on-validation instead of latest)

### C) Hybrid RL+LLM work

- Distill RL policy behavior into LLM prompts
- Use RL checkpoints as strong baseline for mixed-team evaluation
- Analyze where RL policy remains superior vs LLM policy under same scenario slices

## 10) Key Caveat

This training pipeline trains **Cybermonic RL policies**, not LLM weights.

- RL training: `cybermonic_train.py` + PPO/GNN stack
- LLM behavior: configured via `CybORG/Agents/LLMAgents/*` and model backends/prompts — see **`docs/LLM_DEFENDER_AGENT_GUIDE.md`** for construction, YAML configs, and run instructions.

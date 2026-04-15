# Related Papers: Contribution Analysis for "Beyond the Baseline"

**Target Paper:** *Beyond the Baseline: Improving LLM-driven Agents for Autonomous Cyber Defense*  
**Authors:** Baruh Ifraimov, Dor Cohen — Ariel University  
**Date:** April 2026

---

## Overview of Your Paper's Current State

Your paper extends Castro et al.'s "Large Language Models are Autonomous Cyber Defenders" by introducing:

1. **Chain-of-Self-Correction (CoSC)** — an iterative self-verification loop before action commitment.
2. **Schema-Constrained Prompting** — rigid JSON output enforcement to eliminate invalid actions.
3. **Local Inference** — deepseek-r1:8b and gemma4:e4b via Ollama on 8GB VRAM (AMD RX 5700 XT).
4. **Four-stage reasoning pipeline** — Perceive → Reason → Plan → Act.

**Key metrics you target:** Joint Reward (μ), Standard Deviation (σ), MTTR, Hallucination Rate.  
**Baseline gap to close:** KEEP RL (μ = −493) vs. ALL-LLM (μ = −2547.2).

Below, each related paper is analyzed for *concrete, implementable contributions* that can strengthen your extension.

---

## Paper 1: Hierarchical Multi-Agent RL for Cyber Network Defense (Singh et al., 2025)

### What This Paper Offers You

This is your primary RL-baseline reference paper. Beyond providing the red-agent FSM variants you already use, it offers three underutilized resources: (a) the IOC-enhanced observation space design, (b) interpretable defense metrics, and (c) the expert-rule logic that should anchor your CoSC verification.

---

### Contribution 1A: IOC-Enhanced Observation Space for Prompt Engineering

**Paper Title:** Hierarchical Multi-Agent RL for Cyber Network Defense  
**Method Title:** IOC-Prioritized Observation Vector Enhancement

**What it is:** Singh et al. extend CybORG's basic observation vector with Indicators of Compromise (IOCs) per host. They encode three attack-phase priority levels: priority 1 for privilege escalation IOCs (malicious files with root access), priority 2 for exploit-phase IOCs (malicious files with user-level access), and priority 3 for reconnaissance IOCs (decoy accesses from scanning). This enhancement alone produces a 42% reward improvement for RL agents. An additional 11% gain comes from incorporating decoy-access signals.

The observation vector structure is: `[mission_bit | subnet_info (one-hot) | suspicious_processes (binary per host) | suspicious_connections (binary per host) | IOC_priority (0/1/2/3 per host)]`.

**Why it matters for your paper:** Castro et al.'s adapter currently parses CybORG observations into natural language at a relatively coarse level (agent name, mission phase, last action, communication vectors, suspicious activity). You are not extracting IOC-level detail from the CybORG observation object. Since Singh et al. demonstrate that IOC-awareness is the single largest contributor to RL agent performance, encoding these same signals into your LLM prompt could dramatically improve action selection quality.

**Implementation — How To:**

In your Adapter Interface (Section 4.1 of your paper), extend the CybORG observation parser to extract IOC-level fields from the observation dictionary. CybORG provides per-host information about malicious files (including access level) and decoy service accesses. Currently your formatter converts this into generic "Suspicious Activity Detected" strings. Instead, structure the prompt with explicit IOC priority per host:

```
Host: server_0
  IOC Priority: 2 (exploit-phase — malicious file with user-level access)
  Suspicious Processes: True
  Suspicious Connections: False
Host: user_1
  IOC Priority: 0 (no compromise indicators)
Host: user_2
  IOC Priority: 3 (reconnaissance — decoy access detected)
```

This gives the LLM the same information density that enables H-MARL Expert to achieve −129.53 reward. In your Schema-Constrained Prompting JSON output, you can then instruct the LLM: "If any host shows IOC Priority ≥ 1, prioritize Restore or Remove for that host. If IOC Priority = 0 for all hosts, prioritize Monitor or Analyse."

**Where in your paper:** Extend Section 4.1 ("The Adapter Interface"). Add a new paragraph explaining the IOC-enhanced observation parsing. Reference Singh et al. for the design rationale. This is a straightforward code change in your CybORG wrapper.

---

### Contribution 1B: Interpretable Defense Metrics

**Paper Title:** Hierarchical Multi-Agent RL for Cyber Network Defense  
**Method Title:** Multi-Perspective Interpretable Metrics Suite

**What it is:** Singh et al. define seven interpretable metrics beyond cumulative reward, organized into three categories:

*Network Security Posture:*
- **Clean Hosts:** fraction of hosts with no red presence.
- **Non-Escalated Hosts:** fraction of hosts where red has no root sessions.

*Recovery Metrics:*
- **Mean Time to Recover (MTTR):** average consecutive steps a host remains compromised.
- **Recovery Precision:** TP / (TP + FP), where TP = recoveries on actually infected hosts, FP = recoveries on clean hosts.
- **Recovery Error:** FP / (TP + FP).

*Operational Metrics:*
- **Red Impact Count:** number of times the OT service becomes unavailable.

**Key finding:** MARL Decentralized has a recovery precision of only 0.27, while H-MARL Expert achieves the highest recovery precision because its expert rule only invokes the Recover sub-policy when IOCs are present. This reveals that raw reward alone is misleading — an agent can achieve similar rewards through very different (and worse) strategies.

**Why it matters for your paper:** Your current evaluation metrics (Section 4.4) list Joint Reward, σ, MTTR, and Hallucination Rate. You are missing Recovery Precision, Clean Hosts, and Red Impact Count. These additional metrics would strengthen your comparative analysis and might reveal that your CoSC mechanism improves precision even when reward differences are modest. In particular, Recovery Precision directly measures whether your self-correction loop prevents wasteful Restore actions on uncompromised hosts — exactly the kind of hallucination you aim to eliminate.

**Implementation — How To:**

After each episode, iterate through the CybORG state to count per-host compromise status. Track each Restore/Remove action and cross-reference against whether the target host was actually compromised at that timestep. Compute:

```
Recovery Precision = (restores on compromised hosts) / (total restores)
Clean Hosts = (hosts with no red presence) / (total hosts)   [averaged per step]
Red Impact Count = count of steps where OT service was unavailable
```

**Where in your paper:** Add these three metrics to Section 4.4 ("Evaluation Metrics"). In Section 6 ("Experimental Results"), add a table modeled after Singh et al.'s Table 3 that reports these metrics for each model variant you test (deepseek-r1:8b baseline, deepseek-r1:8b + CoSC, gemma4:e4b + CoSC, KEEP RL).

**⚠️ Improvement Suggestion:** Your paper currently does not define MTTR precisely. Singh et al. define it as "mean number of consecutive steps spent in a compromised state." Adopt this definition explicitly. Also, their Table 3 reveals that similar rewards can mask very different defensive behaviors. I recommend you add Recovery Precision as a primary metric alongside Hallucination Rate, since it captures the downstream consequence of hallucinations (wasted recovery = action-level hallucination).

---

### Contribution 1C: Expert IOC Rules as CoSC Reference Logic

**Paper Title:** Hierarchical Multi-Agent RL for Cyber Network Defense  
**Method Title:** IOC-Based Expert Master Policy (Rule-Based Decision Logic)

**What it is:** The H-MARL Expert master policy πE is a deterministic rule:

```
IF malicious-file IOCs detected on host → invoke Recover sub-policy
ELIF network IOCs detected → invoke Control Traffic sub-policy  
ELSE → invoke Investigate sub-policy
```

This simple rule, combined with well-trained sub-policies, achieves the best reward of −129.53 ± 44.60 against the default red agent — outperforming all learned master policies.

**Why it matters for your paper:** Your Chain-of-Self-Correction (Section 4.1) currently checks whether the LLM's proposed action is syntactically valid and logically consistent. You can strengthen CoSC by encoding the IOC expert rule as a *semantic verification layer*. Before committing an action, the CoSC loop should check: "If IOCs were detected and the proposed action is NOT a recovery action (Restore/Remove), flag a potential reasoning error and re-generate."

**Implementation — How To:**

In your CoSC verification prompt, add a rule-based sanity check as a second verification stage:

```
VERIFICATION RULES:
1. Syntax check: Is the proposed action in the valid action set?
2. Semantic check (IOC rule):
   - If ANY host shows malicious file indicators → action MUST target 
     that host with Restore or Remove. If it does not, re-generate.
   - If NO IOCs detected → Analyse or Monitor is acceptable. 
     Restore on a clean host is wasteful — re-generate.
3. Consistency check: Does the reason field logically support the chosen action?
```

This directly transfers Singh et al.'s expert knowledge into your prompt without training. You already state in your paper that the IOC rule "serves as a reference for what correct reasoning looks like." This contribution makes that statement concrete.

**Where in your paper:** Extend Section 4.1 under "Novel Extension — Chain-of-Self-Correction (CoSC)." Add a paragraph describing the IOC-rule verification layer. This is a novel synthesis: you are combining RL domain expertise with LLM self-correction, which neither Singh et al. nor Castro et al. implemented.

---

## Paper 2: Automated Cyber Defense with Generalizable Graph-Based RL Agents (King et al., 2025)

### What This Paper Offers You

This paper introduces the KEEP agent (your RL benchmark) and the GCN-based graph representation of network topology. Its primary contribution to your work is conceptual context — understanding *why* KEEP outperforms LLM agents and what architectural features create that gap.

---

### Contribution 2A: Graph-Based Observation Representation as Prompt Structure

**Paper Title:** Automated Cyber Defense with Generalizable Graph-Based RL Agents  
**Method Title:** Attributed Graph Observation with GCN Node Embeddings

**What it is:** King et al. represent the network as an attributed graph O = ⟨V, E, X⟩ where V = hosts (nodes), E = inter-host communication (edges), and X = per-node feature vectors (compromise status, services, etc.). A 2-layer GCN processes this graph:

$$H^{(\ell+1)} = \sigma\left(\tilde{D}^{-\frac{1}{2}} \tilde{A} \tilde{D}^{-\frac{1}{2}} H^{(\ell)} W^{(\ell)} + b^{(\ell)}\right)$$

where Ã = A + I (adjacency plus self-loops), D̃ = degree matrix, W and b are trainable parameters. The GCN uses 256-dimensional first layer and 64-dimensional second layer. Actions are represented as functions on nodes (a_n(v_i)) rather than fixed-length vectors, enabling generalization across topologies.

The key insight: KEEP's strength comes from *relational inductive bias* — it processes the relationships between hosts, not just their individual states. This is precisely what a flat text prompt fails to capture.

**Why it matters for your paper:** Castro et al.'s observation formatting lists hosts sequentially with no explicit relational structure. The LLM receives "Suspicious Activity: host_3 has suspicious process" but does not see that host_3 connects to host_7 which connects to the OT service. KEEP "sees" this graph structure natively. You can partially close this gap by structuring your prompt to make network topology explicit.

**Implementation — How To:**

In your Adapter Interface, augment the natural language observation with an explicit topology section. CybORG provides subnet structure and connectivity information. Instead of listing hosts flat, structure the prompt to convey the graph:

```
NETWORK TOPOLOGY:
  Restricted Zone A: [server_0, user_0, user_1, user_2]
    → Connected to: Operational Zone A (via router_A)
  Operational Zone A: [server_1, user_3, user_4]
    → Connected to: HQ Admin Network (blocked during Mission B)
    → OT Service hosted on: server_1

CURRENT HOST STATUS:
  server_0: IOC Priority 2 (exploit-phase) — CRITICAL: 1 hop from OT service
  user_1: Clean
  user_3: IOC Priority 3 (reconnaissance) — adjacent to server_1 (OT)
```

The "1 hop from OT service" annotation gives the LLM relational awareness that Castro et al.'s adapter does not provide. This is a lightweight approximation of what KEEP gets from GCN node embeddings — the LLM can now reason: "user_3 is scanning and is adjacent to the critical server, so I should prioritize investigating or isolating user_3."

**Where in your paper:** This enhancement belongs in Section 4.1 ("The Adapter Interface"), specifically as an extension of the observation formatting. Frame it as "topology-aware prompt design inspired by the graph-based observations of King et al."

**⚠️ Improvement Suggestion:** Your Related Work section (Section 3, subsection on King et al.) correctly states that understanding KEEP contextualizes the benchmark. However, you do not currently extract any implementable technique from this paper. Adding the topology-aware prompt structure would make this a contributing reference rather than purely contextual. I recommend adding this to your methodology and explicitly stating it in the Contribution section of the King et al. review.

---

### Contribution 2B: Context-Based POMDP Framing for Evaluation Rigor

**Paper Title:** Automated Cyber Defense with Generalizable Graph-Based RL Agents  
**Method Title:** Context-Based POMDP (CMDP) with Disjoint Train/Test Spaces

**What it is:** King et al. formalize the evaluation using Kirk et al.'s Context-Based POMDP: the set of all possible environments parameterized by a context variable C. They partition the context space into M|C_train and M|C_test, requiring the agent to generalize across the test set using only training experience. Their key result: the inductive GCN model maintains a score of 0.9955 at |V|=40 and degrades gracefully to larger networks, while transductive (fixed-topology) models fail completely on unseen networks.

**Why it matters for your paper:** CybORG CAGE 4 randomizes network topology between episodes (32–128 hosts across 8 subnets). Your LLM agent already has an advantage here since it doesn't memorize a specific topology. However, you should formally acknowledge this as a *zero-shot generalization* property of your LLM approach and compare against KEEP's generalization score. This strengthens the argument that even if your reward is lower, your agent may generalize better across topology variants.

**Implementation — How To:**

Run your evaluation across at least 10 different random network seeds (CybORG randomizes topology per episode). Report per-seed results to show variance across topologies. Compare: KEEP's performance variance across seeds vs. your LLM agent's variance. If the LLM shows lower σ across topology variants, this demonstrates a generalization advantage worth reporting.

**Where in your paper:** Add to Section 6 ("Experimental Results") as a subsection on generalization robustness. Reference King et al.'s CMDP framework and their finding that topology-sensitivity is the main failure mode for RL approaches.

---

## Paper 3: Hallucination-Resistant Security Planning with an LLM (Hammar et al., 2026)

### What This Paper Offers You

This is the most algorithmically rich paper for your extension. It provides the formal theoretical foundation for hallucination control that your CoSC mechanism currently lacks. Three extractable components are critical: the consistency function, the conformal abstention policy, and the calibration procedure.

---

### Contribution 3A: Lookahead Consistency Function

**Paper Title:** Hallucination-Resistant Security Planning with a Large Language Model  
**Method Title:** Lookahead Consistency Function λ(A)

**What it is:** Given N candidate actions A_t = {a¹_t, ..., aᴺ_t}, the LLM predicts for each action the expected time remaining to complete the task, T^i_{t+1}. The consistency of the candidate set is measured as:

$$\lambda(\mathcal{A}_t) = \exp\left(-\frac{\beta}{N} \sum_{i=1}^{N} \left(T^i_{t+1} - \overline{T}_{t+1}\right)^2\right)$$

where β > 0 controls sensitivity and T̄_{t+1} is the mean predicted time. This function outputs a value in [0, 1], where 1 = fully consistent (all candidates predict similar outcomes) and 0 = inconsistent (candidates predict wildly different outcomes). Hammar et al. use β = 0.9 and N = 3 candidate actions.

**Why it matters for your paper:** Your CoSC currently performs a binary check: "Does the action make sense?" The consistency function provides a *continuous confidence score* that quantifies how much the LLM "agrees with itself." If you prompt the LLM 3 times for the same observation and get three different actions with very different predicted outcomes, the inconsistency signals hallucination. This is more principled than a single self-verification pass.

**Implementation — How To:**

Adapt the consistency function for CAGE 4. Since you don't have "time to complete task," use a proxy: prompt the LLM N=3 times for the same observation and ask each time for both an action and a predicted "risk score" (e.g., "On a scale of 1-10, how risky is the network state after this action?"). Then compute:

```python
import math

def consistency(predictions, beta=0.9):
    """
    predictions: list of N predicted risk scores from repeated LLM calls
    Returns: float in [0, 1], higher = more consistent
    """
    N = len(predictions)
    mean_pred = sum(predictions) / N
    variance = sum((p - mean_pred)**2 for p in predictions) / N
    return math.exp(-beta * variance)
```

If λ < γ (threshold), fall back to a safe default action (e.g., Monitor) instead of the proposed action. This implements conformal abstention (Contribution 3B below) within your single-inference-call constraint.

**Practical concern on your hardware:** Running 3 LLM calls per step on an 8GB VRAM GPU triples your already-slow inference. Consider two mitigations: (a) only apply multi-call consistency checking when the observation contains IOCs (i.e., when the decision matters most), or (b) use temperature sampling — make 3 calls with temperature=0.7 from a single batch, which is faster than 3 sequential calls.

**Where in your paper:** Add as a subsection in Section 4.1 under CoSC, specifically as "Consistency-Weighted Self-Correction." Present the formula, explain the adaptation to CAGE 4, and cite Hammar et al. This directly strengthens your theoretical grounding.

---

### Contribution 3B: Conformal Abstention Policy π_γ

**Paper Title:** Hallucination-Resistant Security Planning with a Large Language Model  
**Method Title:** Conformal Abstention Policy with Consistency Threshold γ

**What it is:** The decision policy is:

$$\pi_\gamma(\mathcal{A}_t) = \begin{cases} \emptyset \text{ (abstain)}, & \text{if } \lambda(\mathcal{A}_t) \leq \gamma \\ \arg\min_{a^i_t \in \mathcal{A}_t} \{T^i_{t+1}\}, & \text{if } \lambda(\mathcal{A}_t) > \gamma \end{cases}$$

When consistency is below threshold γ, the system abstains — it does not act. In Hammar et al.'s framework, abstention triggers external feedback collection from a digital twin. In your CAGE 4 context, where no digital twin exists, abstention should map to a safe fallback action.

**The theoretical guarantee (Proposition 1):** Given a calibration dataset of n hallucinated action sets, the threshold γ̃ can be configured such that the probability of non-abstention (i.e., taking a potentially hallucinated action) is bounded by κ:

$$\tilde{\gamma} = \inf\left\{\gamma \ \middle|\ \frac{|\{i \mid \lambda(\mathcal{A}_i) \leq \gamma\}|}{n} \geq \frac{\lceil(n+1)(1-\kappa)\rceil}{n}\right\}$$

$$P\left(\pi_{\tilde{\gamma}}(\tilde{\mathcal{A}}) \neq \emptyset\right) \leq \kappa$$

Hammar et al. use γ = 0.9 calibrated on n = 100 hallucinated examples, achieving a hallucination rate of 0.02 vs. 0.06 without abstention.

**Why it matters for your paper:** Your CoSC currently has no fallback mechanism. If the self-correction loop still produces a bad action, it gets executed. Conformal abstention provides a principled safety net: if the LLM is too uncertain, default to Monitor (a safe, information-gathering action) rather than risk a hallucinated Restore or BlockTraffic.

**Implementation — How To:**

1. **Calibration phase (offline):** Before your main experiments, run 100 episodes where you record every instance where the LLM produces an invalid or clearly wrong action (e.g., Restore on a clean host, BlockTraffic during a phase where it's not allowed). For each, record the consistency score λ from multiple LLM calls on that observation.

2. **Set threshold:** Using the formula above with κ = 0.05, find the γ̃ that ensures at most 5% of non-abstained actions are hallucinated.

3. **Runtime policy:**

```python
def select_action(observation, llm, gamma=0.9, N=3):
    candidates = []
    risk_scores = []
    for _ in range(N):
        response = llm.generate(observation)  # returns action + risk_score
        candidates.append(response['action'])
        risk_scores.append(response['risk_score'])
    
    lam = consistency(risk_scores)
    
    if lam <= gamma:
        return "Monitor", "ABSTAINED: low consistency ({:.2f})".format(lam)
    else:
        # Select the action with lowest predicted risk
        best_idx = risk_scores.index(min(risk_scores))
        return candidates[best_idx], "Consistent ({:.2f})".format(lam)
```

**Where in your paper:** This is a direct extension of your CoSC mechanism. Add it as the final stage of the self-correction pipeline: Perceive → Reason → Plan → CoSC Syntax Check → CoSC Semantic Check (IOC rules) → Consistency Check → Act or Abstain. Present the formula and your adapted calibration procedure in Section 4.1.

---

### Contribution 3C: Formal Hallucination Definition

**Paper Title:** Hallucination-Resistant Security Planning with a Large Language Model  
**Method Title:** Definition 1 — Hallucinated Action (Formal Definition)

**What it is:** Hammar et al. provide a formal definition of hallucination in the security planning context:

> **Definition 1 (Hallucinated action).** Given a sequence of actions a₀, ..., a_{t-1}, a_t for completing a security management task. The action a_t is hallucinated if it does not reduce the expected time remaining to complete the task:
> 
> E{T_{t+1} | a₀, ..., a_t} ≥ E{T_t | a₀, ..., a_{t-1}}

**Why it matters for your paper:** Your paper mentions "hallucination rate" as a metric but does not formally define what constitutes a hallucination in the CAGE 4 context. Adopting this definition, adapted to your reward framework, gives your evaluation rigor.

**Implementation — How To:**

Adapt for CAGE 4: define a hallucinated action as one that does not improve the cumulative reward trajectory. Operationally, classify each action as hallucinated if:

1. **Syntactic hallucination:** The action is not parseable or not in the valid action set (this is what your Schema-Constrained Prompting addresses).
2. **Semantic hallucination:** The action targets a host/subnet that is irrelevant (e.g., Restore on a clean host, Analyse on a host already fully analyzed this step).
3. **Strategic hallucination:** The action is valid and relevant but clearly suboptimal (e.g., Monitor when IOCs indicate active compromise).

Report hallucination rate as the sum of categories 1-3 divided by total actions.

**Where in your paper:** Add this formal definition to Section 4.4 ("Evaluation Metrics") alongside your Hallucination Rate metric. Cite Hammar et al. for the theoretical basis and explain your CAGE 4 adaptation.

---

## Paper 4: In-Context Autonomous Network Incident Response (Gao et al., 2026)

### What This Paper Offers You

Gao et al. provide the most directly transferable architectural blueprint. Your paper already adopts their four-stage pipeline (Perceive → Reason → Plan → Act). Below are three additional contributions you are not yet fully leveraging.

---

### Contribution 4A: LoRA Fine-Tuning for Perception and Reasoning

**Paper Title:** In-Context Autonomous Network Incident Response  
**Method Title:** LoRA-Based Supervised Fine-Tuning for State Estimation

**What it is:** Gao et al. fine-tune a DeepSeek-14B model using LoRA (Low-Rank Adaptation) on 50,000 instruction-answer pairs from CSLE-IncidentResponse-V1. The fine-tuning loss is:

$$L(w) = -\frac{1}{B} \sum_{i=1}^{B} \sum_{k=1}^{\ell_i} \log \Phi_w(y^i_k | x^i, y^i_{1:k-1})$$

where w denotes the LoRA trainable parameters (rank 64), B is the batch size, and ℓ_i is the token length of the i-th answer. Each training pair consists of an instruction (incident details + prompt to assess recovery state) and an answer (ground truth state + chain-of-thought reasoning).

Their ablation study shows that removing fine-tuning increases recovery time by 103%. This is the single largest contributor to their agent's performance.

**Why it matters for your paper:** You currently use deepseek-r1:8b and gemma4:e4b as-is with 4-bit quantization. No fine-tuning is applied. This means your models lack CybORG-specific reasoning capabilities. Even lightweight LoRA fine-tuning (which only trains ~0.5% of parameters) on CAGE 4 observation-action pairs could substantially improve action selection quality.

**Implementation — How To:**

1. **Generate training data:** Run KEEP (your RL baseline) for 500 episodes, recording at each step: (a) the natural-language observation (from your adapter), (b) the action KEEP selected, and (c) a chain-of-thought explanation you generate by analyzing the observation-action pair (e.g., "Host server_0 shows malicious files with user access (IOC Priority 2). The correct action is Remove server_0 to eliminate the malware before privilege escalation occurs.").

2. **Fine-tune with LoRA on your hardware:**

```python
# Using unsloth for efficient LoRA fine-tuning on 8GB VRAM
from unsloth import FastLanguageModel

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="deepseek-ai/deepseek-r1-distill-qwen-8b",  # or via Ollama export
    max_seq_length=2048,
    load_in_4bit=True,  # fits in 8GB VRAM
)

model = FastLanguageModel.get_peft_model(
    model,
    r=16,              # LoRA rank (lower than Gao's 64 due to VRAM constraint)
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    lora_alpha=16,
    lora_dropout=0.05,
)
```

3. **Training data format:**
```json
{
    "instruction": "You are defending subnet Restricted Zone A. Current observation:\nHost server_0: IOC Priority 2, suspicious processes detected\nHost user_1: Clean\nMission Phase: 1\nWhat action should you take and why?",
    "output": "Analysis: server_0 has user-level malicious files (IOC Priority 2), indicating an active exploit. No other hosts show compromise. Action: Remove server_0. Reason: Removing malicious processes prevents escalation to root access while keeping the host operational, unlike Restore which would cause service disruption."
}
```

**Practical note:** Fine-tuning on CAGE 4 data generated from KEEP's decisions effectively distills RL expertise into your LLM, which directly addresses the performance gap without requiring RL training infrastructure. Gao et al.'s ablation shows this is the most impactful single improvement.

**Where in your paper:** This would be a significant addition to Section 4.2 ("Local Training and Inference Setup"). Frame it as "RL-Distilled LoRA Fine-Tuning" — a technique that transfers KEEP's domain expertise into the LLM through behavioral cloning on CAGE 4 trajectories.

**⚠️ Important Note:** This is a substantial implementation effort. If time-constrained, you could alternatively run a smaller-scale experiment (e.g., 5,000 training pairs) and report it as a preliminary result. Even partial fine-tuning is likely to show measurable improvement.

---

### Contribution 4B: Monte-Carlo Lookahead Planning (Adapted)

**Paper Title:** In-Context Autonomous Network Incident Response  
**Method Title:** Online Conjectural Lookahead Planning (Algorithm 1)

**What it is:** At each step, the LLM agent: (1) generates N candidate actions, (2) for each candidate, simulates M future trajectories using the LLM as a world model, (3) computes the expected cost Q(ŝ_t, â^k_t) as a sample average over simulated trajectories, and (4) selects the action minimizing Q:

$$Q(\hat{s}_{t+1}, \hat{a}^k_{t+1}) = \frac{1}{M} \sum_{i \in [M]} \sum_{(\hat{s}, \hat{a}) \in q^i} c(\hat{s}, \hat{a})$$

$$a_{t+1} \in \arg\min_{a \in \mathcal{A}_t} Q(\hat{s}_{t+1}, a)$$

The complete algorithm (Algorithm 1 in Gao et al.) includes an in-context adaptation step where predicted alerts are compared to actual alerts after execution. If they diverge significantly, the attack model conjecture θ̂ is updated via a frontier LLM call.

**Why it matters for your paper:** Full Monte-Carlo lookahead is too expensive for your hardware (Gao et al. report ~20 minutes per 5-action plan on an A100). However, a simplified 1-step lookahead is feasible and aligns with your CoSC framework.

**Implementation — How To (Simplified 1-Step Lookahead):**

Instead of full tree search, implement a lightweight version: for each of N=3 candidate actions, ask the LLM to predict the next observation. Pick the action whose predicted next-observation looks least compromised.

In your prompt, after generating the candidate action:

```
LOOKAHEAD VERIFICATION:
Given the current observation and your proposed action [Remove server_0]:
1. Predict: What will the network state look like in the NEXT step?
   Expected: server_0 should show no malicious processes. Other hosts unchanged.
2. Does this prediction seem reasonable? (yes/no)
3. If no, suggest an alternative action.
```

This is computationally cheap (one extra prompt turn, not M*N rollouts) and captures the essence of Gao et al.'s planning stage within your single-inference constraint.

**Where in your paper:** Integrate into Section 4.1 under the "Planning" stage of your Perceive → Reason → Plan → Act pipeline. Frame it as "Simplified Lookahead Verification" inspired by Gao et al.'s Monte-Carlo planning, adapted for resource-constrained local inference.

---

### Contribution 4C: In-Context Tactic Recalibration

**Paper Title:** In-Context Autonomous Network Incident Response  
**Method Title:** In-Context Adaptation via Alert Divergence Detection

**What it is:** After executing an action, the agent compares predicted alerts (ô_{t+1}) with actual alerts (o_{t+1}). If there is significant divergence, the agent recalibrates its conjecture of the attack tactic θ̂ and re-plans. In Gao et al., this recalibration uses a frontier model (GPT-5.2) to interpret the divergence.

**Why it matters for your paper:** Your LLM agent currently processes each step independently — it does not track whether its predictions are matching reality. By maintaining a running accuracy score of "predicted next-step vs. actual next-step," you can detect when the model's reasoning is drifting and trigger more aggressive self-correction.

**Implementation — How To:**

Maintain a sliding window of the last 5 steps. At each step, record what the LLM predicted would happen vs. what actually happened. If accuracy drops below 60%, inject an additional context line into the prompt:

```
WARNING: Your recent predictions have been inaccurate (3/5 incorrect). 
The attack pattern may have changed. Re-assess the threat landscape 
before selecting your next action. Focus on Monitor/Analyse actions 
to gather fresh intelligence before committing to recovery actions.
```

This is a lightweight adaptation of Gao et al.'s recalibration that works within a single-model, single-call framework.

**Where in your paper:** Add to Section 4.1 under the "Reasoning" stage. Frame it as "Prediction-Accuracy Monitoring" — a rolling self-assessment that triggers cautious re-investigation when the model's world understanding diverges from observations.

---

## Consolidated Implementation Roadmap

Below is a prioritized list of contributions, ranked by estimated impact relative to implementation effort, mapped to your paper's sections.

| Priority | Contribution | Source Paper | Target Section | Est. Impact | Est. Effort |
|----------|-------------|-------------|----------------|-------------|-------------|
| 1 | IOC-Enhanced Observation Parsing | Singh et al. (1A) | §4.1 Adapter | HIGH | LOW |
| 2 | Formal Hallucination Definition | Hammar et al. (3C) | §4.4 Metrics | MEDIUM | LOW |
| 3 | Interpretable Metrics (Precision, Clean Hosts) | Singh et al. (1B) | §4.4, §6 | MEDIUM | LOW |
| 4 | IOC Expert Rules in CoSC | Singh et al. (1C) | §4.1 CoSC | HIGH | LOW |
| 5 | Topology-Aware Prompt Structure | King et al. (2A) | §4.1 Adapter | MEDIUM | MEDIUM |
| 6 | Consistency Function λ(A) | Hammar et al. (3A) | §4.1 CoSC | HIGH | MEDIUM |
| 7 | Conformal Abstention Policy π_γ | Hammar et al. (3B) | §4.1 CoSC | HIGH | MEDIUM |
| 8 | 1-Step Lookahead Verification | Gao et al. (4B) | §4.1 Planning | MEDIUM | MEDIUM |
| 9 | Prediction-Accuracy Monitoring | Gao et al. (4C) | §4.1 Reasoning | MEDIUM | LOW |
| 10 | LoRA Fine-Tuning on CAGE 4 Data | Gao et al. (4A) | §4.2 Training | VERY HIGH | HIGH |
| 11 | Generalization Robustness Evaluation | King et al. (2B) | §6 Results | MEDIUM | LOW |

---

## Questions and Suggested Improvements

Based on my analysis, I have the following observations and questions:

**1. Missing DATASET Section:** Your Section 5 ("DATASET") is empty. Since you are working within CybORG CAGE 4 (which is a simulation environment, not a traditional dataset), I recommend restructuring this section as "Simulation Environment and Data Collection." Describe (a) CybORG CAGE 4 parameters (network size, episode length, randomization), (b) how you collect evaluation data (number of episodes, seeds, red agent variants), and (c) if you pursue LoRA fine-tuning, describe the training data generation process. Would you like me to draft this section?

**2. Your CoSC needs formal specification.** Currently the CoSC is described narratively. I recommend adding pseudocode (Algorithm 1 in your paper) similar to Gao et al.'s Algorithm 1 format. This makes it reproducible. Shall I draft this?

**3. The consistency function triples inference time.** On your 8GB GPU, running 3 LLM calls per step is expensive. You might consider a compromise: run full consistency checking only during the first 50 steps of each episode (when the red agent is most active) and use single-call CoSC for the remaining 450 steps. This is an engineering decision — would you like to discuss tradeoffs?

**4. Your Related Work table (Table I) is well-structured** but could benefit from an additional column: "Directly Used In Our Extension" (Yes/No + brief description). This makes the contribution mapping explicit for reviewers.

**5. The abstract placeholder** "[insert your specific extension here]" needs to be replaced. Based on your methodology, I suggest: "...through an optimized Chain-of-Self-Correction (CoSC) prompting strategy that integrates IOC-aware reasoning rules, consistency-based hallucination detection, and schema-constrained output enforcement, benchmarked across next-generation reasoning models (DeepSeek-R1:8b, Gemma4:e4b) running on consumer hardware."

Let me know which of these you'd like me to help develop further.

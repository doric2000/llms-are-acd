# LLM Model Comparison

Generated at: 2026-04-16T11:06:10
Profile: quick
Baseline lock: max_eps=2, episode_length=500
Matrix mode: paper

## Aggregate By Model

| Model | Cases | Failed Cases | Mean Reward | Reward StdDev | Hallucination Rate |
|---|---:|---:|---:|---:|---:|
| qwen2.5-7b | 8 | 0 | -12.6833 | 1.8593 | 0.026293 |

## Case Results

| Model | Case | Red Variant | Scenario ID | Scenario Seed | Return Code | Mean Reward | Hallucination Rate | Elapsed |
|---|---|---|---|---:|---:|---:|---:|---|
| qwen2.5-7b | red-aggressive__blue-s1 | aggressive | scenario_1 | 101 | 0 | -15.2000 | 0.028736 | 0:08:02.625368 |
| qwen2.5-7b | red-aggressive__blue-s2 | aggressive | scenario_2 | 102 | 0 | -12.8000 | 0.036782 | 0:07:46.863348 |
| qwen2.5-7b | red-aggressive__blue-s3 | aggressive | scenario_3 | 103 | 0 | -15.0667 | 0.025287 | 0:07:47.288074 |
| qwen2.5-7b | red-aggressive__blue-s4 | aggressive | scenario_4 | 104 | 0 | -12.9000 | 0.024138 | 0:07:41.679252 |
| qwen2.5-7b | red-stealthy__blue-s1 | stealthy | scenario_1 | 101 | 0 | -10.1000 | 0.027586 | 0:07:30.631206 |
| qwen2.5-7b | red-stealthy__blue-s2 | stealthy | scenario_2 | 102 | 0 | -13.2333 | 0.029885 | 0:07:36.981754 |
| qwen2.5-7b | red-stealthy__blue-s3 | stealthy | scenario_3 | 103 | 0 | -11.2000 | 0.012644 | 0:07:34.302224 |
| qwen2.5-7b | red-stealthy__blue-s4 | stealthy | scenario_4 | 104 | 0 | -10.9667 | 0.025287 | 0:07:38.723490 |

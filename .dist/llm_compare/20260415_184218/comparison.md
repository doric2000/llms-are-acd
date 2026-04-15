# LLM Model Comparison

Generated at: 2026-04-15T18:45:29
Profile: quick
Baseline lock: max_eps=2, episode_length=500
Matrix mode: paper

## Aggregate By Model

| Model | Cases | Failed Cases | Mean Reward | Reward StdDev | Hallucination Rate |
|---|---:|---:|---:|---:|---:|
| deepseek-r1-1.5b | 8 | 4 | -0.8750 | 0.6292 | 0.281250 |

## Case Results

| Model | Case | Red Variant | Scenario ID | Scenario Seed | Return Code | Mean Reward | Hallucination Rate | Elapsed |
|---|---|---|---|---:|---:|---:|---:|---|
| deepseek-r1-1.5b | red-aggressive__blue-s1 | aggressive | scenario_1 | 101 | 0 | -1.0000 | 0.000000 | 0:00:13.248601 |
| deepseek-r1-1.5b | red-aggressive__blue-s2 | aggressive | scenario_2 | 102 | 0 | 0.0000 | 0.625000 | 0:00:17.948333 |
| deepseek-r1-1.5b | red-aggressive__blue-s3 | aggressive | scenario_3 | 103 | 0 | -1.5000 | 0.250000 | 0:00:14.032968 |
| deepseek-r1-1.5b | red-aggressive__blue-s4 | aggressive | scenario_4 | 104 | 1 | n/a | n/a | n/a |
| deepseek-r1-1.5b | red-stealthy__blue-s1 | stealthy | scenario_1 | 101 | 1 | n/a | n/a | n/a |
| deepseek-r1-1.5b | red-stealthy__blue-s2 | stealthy | scenario_2 | 102 | 1 | n/a | n/a | n/a |
| deepseek-r1-1.5b | red-stealthy__blue-s3 | stealthy | scenario_3 | 103 | 0 | -1.0000 | 0.250000 | 0:00:14.649161 |
| deepseek-r1-1.5b | red-stealthy__blue-s4 | stealthy | scenario_4 | 104 | 1 | n/a | n/a | n/a |

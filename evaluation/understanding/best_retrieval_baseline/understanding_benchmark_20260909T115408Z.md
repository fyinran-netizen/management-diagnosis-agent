# Understanding Strategy × Best Retrieval Baseline

## Benchmark information

- Timestamp (UTC): `2026-09-09T11:54:08Z`
- Cases: `48`
- Top K: `20`
- Case file (reused): `D:\management_diagnosis_agent\evaluation\retrieval\cases\retrieval_cases.json`
- JSON report: `D:\management_diagnosis_agent\evaluation\understanding\best_retrieval_baseline\understanding_benchmark_20260909T115408Z.json`
- Retrieval: metadata-enhanced BM25 + base embedding + linear hybrid; reranker and generation disabled.

## Aggregate metrics

Delta = rule_based − raw.

| Strategy | Hit@1 | Hit@3 | Hit@5 | Recall@5 | Recall@10 | MRR@5 | nDCG@5 | nDCG@10 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Raw | 0.375 | 0.750 | 0.875 | 0.521 | 0.667 | 0.567 | 0.457 | 0.522 |
| Rule-based | 0.396 | 0.750 | 0.854 | 0.465 | 0.590 | 0.576 | 0.428 | 0.484 |
| Delta (rule_based − raw) | +0.021 | +0.000 | -0.021 | -0.056 | -0.076 | +0.009 | -0.030 | -0.039 |

## Configuration

- rule_based goal: `Please identify the main management problems, analyze possible root causes, and provide practical next-step recommendations.`
- Each case runs raw and rule_based independently through `understand_query(...)`, then the resulting retrieval query through `retrieve_relevant_chunks(...)`.
- No LangGraph, generation, reranker, or case-file copy is used.

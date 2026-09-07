# Reranking Benchmark Summary

## Benchmark information

- Timestamp (UTC): `2026-09-05T12:15:42Z`
- Cases: `48`
- Candidate top K: `100`
- Final top K: `20`
- Case file: `D:\management_diagnosis_agent\evaluation\retrieval\cases\retrieval_cases.json`
- JSON report: `D:\management_diagnosis_agent\evaluation\retrieval\reports\reranking_benchmark_20260905T121542Z.json`

## Configuration

Both strategies use the same cases, candidate_top_k, final_top_k, and linear hybrid weights.

| Strategy | Configuration |
| --- | --- |
| `Baseline (linear hybrid)` | candidate_top_k=`100`, final_top_k=`20`, keyword_weight=`0.15`, embedding_weight=`0.85`, hybrid_candidate_k=`500`, use_reranker=`False` |
| `Rerank (linear hybrid + BGE)` | candidate_top_k=`100`, final_top_k=`20`, keyword_weight=`0.15`, embedding_weight=`0.85`, hybrid_candidate_k=`500`, use_reranker=`True`, reranker=`BAAI/bge-reranker-base` |

## Baseline vs rerank

Best values are bolded.

| Strategy | Hit@1 | Hit@3 | Hit@5 | Recall@5 | Recall@10 | Precision@5 | MRR@5 | nDCG@5 | nDCG@10 |
| --- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `Baseline (linear hybrid)` | **0.375** | **0.750** | **0.875** | **0.521** | **0.660** | **0.312** | **0.567** | **0.457** | **0.519** |
| `Rerank (linear hybrid + BGE)` | 0.312 | 0.604 | 0.708 | 0.382 | 0.576 | 0.229 | 0.457 | 0.343 | 0.431 |

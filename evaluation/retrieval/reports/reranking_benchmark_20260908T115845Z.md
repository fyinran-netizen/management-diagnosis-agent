# Reranking Benchmark Summary

## Benchmark information

- Timestamp (UTC): `2026-09-08T11:58:45Z`
- Cases: `48`
- Hybrid candidate K: `20`
- Final K: `10`
- Source retrieval K: `None`
- Case file: `D:\management_diagnosis_agent\evaluation\retrieval\cases\retrieval_cases.json`
- JSON report: `D:\management_diagnosis_agent\evaluation\retrieval\reports\reranking_benchmark_20260908T115845Z.json`

## Configuration

Baseline = Hybrid 原排序。
Hybrid + Rerank = 同一候选集经过 BGE 重排。
Both strategies use the same hybrid candidate pool and linear hybrid weights; Hybrid retrieval runs once per case.

| Strategy | Configuration |
| --- | --- |
| `Baseline (linear hybrid)` | hybrid_candidate_k=`20`, final_k=`10`, source_retrieval_k=`None`, keyword_weight=`0.15`, embedding_weight=`0.85`, use_reranker=`False` |
| `Rerank (linear hybrid + BGE)` | hybrid_candidate_k=`20`, final_k=`10`, source_retrieval_k=`None`, keyword_weight=`0.15`, embedding_weight=`0.85`, use_reranker=`True`, reranker=`BAAI/bge-reranker-base` |

## Baseline vs rerank

Best values are bolded.

| Strategy | Hit@1 | Hit@3 | Hit@5 | Recall@5 | Recall@10 | MRR@5 | nDCG@5 | nDCG@10 |
| --- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `Baseline (linear hybrid)` | **0.375** | **0.750** | **0.875** | **0.521** | **0.667** | **0.567** | **0.457** | **0.522** |
| `Rerank (linear hybrid + BGE)` | 0.354 | 0.667 | 0.771 | 0.444 | 0.618 | 0.510 | 0.398 | 0.479 |

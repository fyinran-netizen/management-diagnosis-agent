# Retrieval Benchmark Summary

## Benchmark information

- Timestamp (UTC): `2026-09-25T06:48:54Z`
- Cases: `48`
- Top K: `20`
- Case file: `D:\management_diagnosis_agent\evaluation\retrieval\cases\retrieval_cases.json`
- JSON report: `evaluation\chunking_retrieval_baseline\retrieval_benchmark_20260925T064854Z.json`

## Retrieval method configurations

| Method | Configuration |
| --- | --- |
| `linear_hybrid` | top_k=`20`, ks=`[1, 3, 5, 10, 20]`, keyword_weight=`0.35`, embedding_weight=`0.65`, candidate_k=`100`, corpus_dir=`data\chunking_strategy_experiments\section_semantic_overlap\overlap_180\corpus`, index_dir=`data\chunking_strategy_experiments\section_semantic_overlap\overlap_180\vector_index`, bm25_metadata_mode=`unweighted` |

## Summary

Best values are bolded.

| Method | Hit@1 | Hit@3 | Hit@5 | Recall@5 | Recall@10 | MRR@5 | nDCG@5 | nDCG@10 | Evidence Coverage@5 | Evidence Density@5 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `linear_hybrid` | **0.625** | **0.792** | **0.896** | **0.573** | **0.753** | **0.727** | **0.527** | **0.602** | **0.542** | **0.074** |

# Retrieval Benchmark Summary

## Benchmark information

- Timestamp (UTC): `2026-09-25T06:57:19Z`
- Cases: `48`
- Top K: `20`
- Case file: `D:\management_diagnosis_agent\evaluation\retrieval\cases\retrieval_cases.json`
- JSON report: `evaluation\chunking_retrieval_baseline\retrieval_benchmark_20260925T065719Z.json`

## Retrieval method configurations

| Method | Configuration |
| --- | --- |
| `linear_hybrid` | top_k=`20`, ks=`[1, 3, 5, 10, 20]`, keyword_weight=`0.15`, embedding_weight=`0.85`, candidate_k=`100`, corpus_dir=`data\chunking_strategy_experiments\section_semantic_overlap\overlap_180\corpus`, index_dir=`data\chunking_strategy_experiments\section_semantic_overlap\overlap_180\vector_index`, bm25_metadata_mode=`unweighted` |
| `rrf_hybrid` | top_k=`20`, ks=`[1, 3, 5, 10, 20]`, rrf_k=`60.0`, candidate_k=`100` |

## Summary

Best values are bolded.

| Method | Hit@1 | Hit@3 | Hit@5 | Recall@5 | Recall@10 | MRR@5 | nDCG@5 | nDCG@10 | Evidence Coverage@5 | Evidence Density@5 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `linear_hybrid` | **0.583** | **0.833** | 0.896 | 0.576 | **0.760** | **0.708** | 0.514 | **0.593** | 0.551 | **0.077** |
| `rrf_hybrid` | 0.542 | 0.833 | **0.917** | **0.615** | 0.753 | 0.685 | **0.527** | 0.587 | **0.572** | 0.077 |

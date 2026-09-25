# Retrieval Benchmark Summary

## Benchmark information

- Timestamp (UTC): `2026-09-25T06:44:33Z`
- Cases: `48`
- Top K: `20`
- Case file: `D:\management_diagnosis_agent\evaluation\retrieval\cases\retrieval_cases.json`
- JSON report: `D:\management_diagnosis_agent\evaluation\retrieval\reports\retrieval_benchmark_20260925T064433Z.json`

## Retrieval method configurations

| Method | Configuration |
| --- | --- |
| `linear_hybrid` | top_k=`20`, ks=`[1, 3, 5, 10, 20]`, keyword_weight=`0.15`, embedding_weight=`0.85`, candidate_k=`100`, corpus_dir=`data\chunking_strategy_experiments\section_semantic_overlap\overlap_180\corpus`, index_dir=`data\chunking_strategy_experiments\section_semantic_overlap\overlap_180\vector_index`, bm25_metadata_mode=`base` |

## Summary

Best values are bolded.

| Method | Hit@1 | Hit@3 | Hit@5 | Recall@5 | Recall@10 | MRR@5 | nDCG@5 | nDCG@10 | Evidence Coverage@5 | Evidence Density@5 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `linear_hybrid` | **0.479** | **0.750** | **0.875** | **0.576** | **0.747** | **0.626** | **0.481** | **0.554** | **0.558** | **0.077** |

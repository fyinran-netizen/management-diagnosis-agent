# Retrieval Benchmark Summary

## Benchmark information

- Timestamp (UTC): `2026-09-25T06:48:39Z`
- Cases: `48`
- Top K: `20`
- Case file: `D:\management_diagnosis_agent\evaluation\retrieval\cases\retrieval_cases.json`
- JSON report: `evaluation\chunking_retrieval_baseline\retrieval_benchmark_20260925T064839Z.json`

## Retrieval method configurations

| Method | Configuration |
| --- | --- |
| `linear_hybrid` | top_k=`20`, ks=`[1, 3, 5, 10, 20]`, keyword_weight=`0.25`, embedding_weight=`0.75`, candidate_k=`100`, corpus_dir=`data\chunking_strategy_experiments\section_semantic_overlap\overlap_180\corpus`, index_dir=`data\chunking_strategy_experiments\section_semantic_overlap\overlap_180\vector_index`, bm25_metadata_mode=`unweighted` |

## Summary

Best values are bolded.

| Method | Hit@1 | Hit@3 | Hit@5 | Recall@5 | Recall@10 | MRR@5 | nDCG@5 | nDCG@10 | Evidence Coverage@5 | Evidence Density@5 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `linear_hybrid` | **0.583** | **0.812** | **0.875** | **0.566** | **0.760** | **0.708** | **0.514** | **0.595** | **0.536** | **0.074** |

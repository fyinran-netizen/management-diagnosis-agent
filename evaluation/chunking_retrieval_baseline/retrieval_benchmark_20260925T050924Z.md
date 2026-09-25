# Retrieval Benchmark Summary

## Benchmark information

- Timestamp (UTC): `2026-09-25T05:09:24Z`
- Cases: `48`
- Top K: `20`
- Case file: `D:\management_diagnosis_agent\evaluation\retrieval\cases\retrieval_cases.json`
- JSON report: `evaluation\chunking_retrieval_baseline\retrieval_benchmark_20260925T050924Z.json`

## Retrieval method configurations

| Method | Configuration |
| --- | --- |
| `bm25` | top_k=`20`, ks=`[1, 3, 5, 10, 20]`, metadata_mode=`unweighted`, corpus_dir=`data\chunking_strategy_experiments\section_semantic_overlap\overlap_180\corpus` |
| `embedding` | top_k=`20`, ks=`[1, 3, 5, 10, 20]`, index_dir=`data\chunking_strategy_experiments\section_semantic_overlap\overlap_180\vector_index`, embedding_model=`BAAI/bge-small-zh-v1.5` |
| `linear_hybrid` | top_k=`20`, ks=`[1, 3, 5, 10, 20]`, keyword_weight=`0.15`, embedding_weight=`0.85`, candidate_k=`100`, corpus_dir=`data\chunking_strategy_experiments\section_semantic_overlap\overlap_180\corpus`, index_dir=`data\chunking_strategy_experiments\section_semantic_overlap\overlap_180\vector_index`, bm25_metadata_mode=`unweighted` |

## Summary

Best values are bolded.

| Method | Hit@1 | Hit@3 | Hit@5 | Recall@5 | Recall@10 | MRR@5 | nDCG@5 | nDCG@10 | Evidence Coverage@5 | Evidence Density@5 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `bm25` | 0.458 | 0.667 | 0.750 | 0.406 | 0.583 | 0.573 | 0.381 | 0.461 | 0.354 | 0.046 |
| `embedding` | 0.333 | 0.604 | 0.750 | 0.462 | 0.635 | 0.486 | 0.384 | 0.461 | 0.443 | 0.063 |
| `linear_hybrid` | **0.500** | **0.708** | **0.896** | **0.576** | **0.750** | **0.641** | **0.487** | **0.564** | **0.551** | **0.076** |

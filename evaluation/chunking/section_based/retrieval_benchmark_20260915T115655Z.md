# Retrieval Benchmark Summary

## Benchmark information

- Timestamp (UTC): `2026-09-15T11:56:55Z`
- Cases: `48`
- Top K: `20`
- Case file: `D:\management_diagnosis_agent\evaluation\retrieval\cases\retrieval_cases.json`
- JSON report: `D:\management_diagnosis_agent\evaluation\chunking\section_based\retrieval_benchmark_20260915T115655Z.json`

## Retrieval method configurations

| Method | Configuration |
| --- | --- |
| `bm25` | top_k=`20`, ks=`[1, 3, 5, 10, 20]`, metadata_mode=`base`, corpus_dir=`D:\management_diagnosis_agent\data\chunking_strategy_experiments\section_based\corpus` |
| `embedding` | top_k=`20`, ks=`[1, 3, 5, 10, 20]`, index_dir=`D:\management_diagnosis_agent\data\chunking_strategy_experiments\section_based\vector_index`, embedding_model=`BAAI/bge-small-zh-v1.5` |
| `linear_hybrid` | top_k=`20`, ks=`[1, 3, 5, 10, 20]`, keyword_weight=`0.15`, embedding_weight=`0.85`, candidate_k=`100`, corpus_dir=`D:\management_diagnosis_agent\data\chunking_strategy_experiments\section_based\corpus`, index_dir=`D:\management_diagnosis_agent\data\chunking_strategy_experiments\section_based\vector_index`, bm25_metadata_mode=`base` |

## Summary

Best values are bolded.

| Method | Hit@1 | Hit@3 | Hit@5 | Recall@5 | Recall@10 | MRR@5 | nDCG@5 | nDCG@10 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `bm25` | **0.312** | 0.625 | 0.646 | 0.326 | 0.542 | 0.443 | 0.311 | 0.409 |
| `embedding` | 0.146 | 0.562 | 0.729 | 0.396 | 0.569 | 0.360 | 0.311 | 0.388 |
| `linear_hybrid` | 0.292 | **0.750** | **0.854** | **0.493** | **0.632** | **0.518** | **0.422** | **0.485** |

# Retrieval Benchmark Summary

## Benchmark information

- Timestamp (UTC): `2026-09-17T05:14:11Z`
- Cases: `48`
- Top K: `20`
- Case file: `D:\management_diagnosis_agent\evaluation\retrieval\cases\retrieval_cases.json`
- JSON report: `D:\management_diagnosis_agent\evaluation\chunking\fixed_size_900\retrieval_benchmark_20260917T051411Z.json`

## Retrieval method configurations

| Method | Configuration |
| --- | --- |
| `bm25` | top_k=`20`, ks=`[1, 3, 5, 10, 20]`, metadata_mode=`base`, corpus_dir=`D:\management_diagnosis_agent\data\chunking_strategy_experiments\fixed_size_900\corpus` |
| `embedding` | top_k=`20`, ks=`[1, 3, 5, 10, 20]`, index_dir=`D:\management_diagnosis_agent\data\chunking_strategy_experiments\fixed_size_900\vector_index`, embedding_model=`BAAI/bge-small-zh-v1.5` |
| `linear_hybrid` | top_k=`20`, ks=`[1, 3, 5, 10, 20]`, keyword_weight=`0.15`, embedding_weight=`0.85`, candidate_k=`100`, corpus_dir=`D:\management_diagnosis_agent\data\chunking_strategy_experiments\fixed_size_900\corpus`, index_dir=`D:\management_diagnosis_agent\data\chunking_strategy_experiments\fixed_size_900\vector_index`, bm25_metadata_mode=`base` |

## Summary

Best values are bolded.

| Method | Hit@1 | Hit@3 | Hit@5 | Recall@5 | Recall@10 | MRR@5 | nDCG@5 | nDCG@10 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `bm25` | 0.333 | 0.625 | 0.750 | 0.361 | 0.604 | 0.486 | 0.309 | 0.408 |
| `embedding` | 0.312 | 0.625 | 0.667 | 0.333 | 0.569 | 0.455 | 0.294 | 0.391 |
| `linear_hybrid` | **0.354** | **0.667** | **0.812** | **0.479** | **0.684** | **0.529** | **0.389** | **0.477** |

## Chunking diagnostics

| Metric | Value |
| --- | ---: |
| Chunk count | 135 |
| Mean length | 883.92 |
| Median length | 900 |
| P95 length | 900 |
| Min length | 56 |
| Max length | 900 |
| Total chunk chars | 119329 |
| Total overlap chars | 5 |
| Overlap ratio | 0.0000 |
| Embedding index build time (ms) | 17522.76 |
| Average retrieval latency (ms) | 15.58 |

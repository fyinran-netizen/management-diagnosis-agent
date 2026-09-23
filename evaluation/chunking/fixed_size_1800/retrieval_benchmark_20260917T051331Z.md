# Retrieval Benchmark Summary

## Benchmark information

- Timestamp (UTC): `2026-09-17T05:13:31Z`
- Cases: `48`
- Top K: `20`
- Case file: `D:\management_diagnosis_agent\evaluation\retrieval\cases\retrieval_cases.json`
- JSON report: `D:\management_diagnosis_agent\evaluation\chunking\fixed_size_1800\retrieval_benchmark_20260917T051331Z.json`

## Retrieval method configurations

| Method | Configuration |
| --- | --- |
| `bm25` | top_k=`20`, ks=`[1, 3, 5, 10, 20]`, metadata_mode=`base`, corpus_dir=`D:\management_diagnosis_agent\data\chunking_strategy_experiments\fixed_size_1800\corpus` |
| `embedding` | top_k=`20`, ks=`[1, 3, 5, 10, 20]`, index_dir=`D:\management_diagnosis_agent\data\chunking_strategy_experiments\fixed_size_1800\vector_index`, embedding_model=`BAAI/bge-small-zh-v1.5` |
| `linear_hybrid` | top_k=`20`, ks=`[1, 3, 5, 10, 20]`, keyword_weight=`0.15`, embedding_weight=`0.85`, candidate_k=`100`, corpus_dir=`D:\management_diagnosis_agent\data\chunking_strategy_experiments\fixed_size_1800\corpus`, index_dir=`D:\management_diagnosis_agent\data\chunking_strategy_experiments\fixed_size_1800\vector_index`, bm25_metadata_mode=`base` |

## Summary

Best values are bolded.

| Method | Hit@1 | Hit@3 | Hit@5 | Recall@5 | Recall@10 | MRR@5 | nDCG@5 | nDCG@10 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `bm25` | 0.458 | **0.812** | 0.875 | 0.552 | 0.729 | 0.626 | 0.429 | 0.504 |
| `embedding` | 0.458 | 0.646 | 0.792 | 0.451 | 0.649 | 0.572 | 0.371 | 0.445 |
| `linear_hybrid` | **0.500** | 0.750 | **0.896** | **0.611** | **0.809** | **0.647** | **0.466** | **0.549** |

## Chunking diagnostics

| Metric | Value |
| --- | ---: |
| Chunk count | 68 |
| Mean length | 1754.71 |
| Median length | 1780.50 |
| P95 length | 1800 |
| Min length | 56 |
| Max length | 1800 |
| Total chunk chars | 119320 |
| Total overlap chars | 0 |
| Overlap ratio | 0.0000 |
| Embedding index build time (ms) | 14429.79 |
| Average retrieval latency (ms) | 16.39 |

# Retrieval Benchmark Summary

## Benchmark information

- Timestamp (UTC): `2026-09-15T13:32:35Z`
- Cases: `48`
- Top K: `20`
- Case file: `D:\management_diagnosis_agent\evaluation\retrieval\cases\retrieval_cases.json`
- JSON report: `D:\management_diagnosis_agent\evaluation\chunking\section_based\retrieval_benchmark_20260915T133235Z.json`

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
| `bm25` | 0.396 | 0.646 | 0.708 | 0.365 | 0.590 | 0.514 | 0.337 | 0.431 |
| `embedding` | 0.271 | 0.604 | 0.729 | 0.451 | 0.611 | 0.434 | 0.364 | 0.432 |
| `linear_hybrid` | **0.417** | **0.771** | **0.854** | **0.549** | **0.681** | **0.594** | **0.467** | **0.523** |

## Chunking diagnostics

| Metric | Value |
| --- | ---: |
| Chunk count | 174 |
| Mean length | 719.11 |
| Median length | 795.50 |
| P95 length | 892 |
| Min length | 91 |
| Max length | 1189 |
| Total chunk chars | 125126 |
| Total overlap chars | 11820 |
| Overlap ratio | 0.0945 |
| Embedding index build time (ms) | 13238.39 |
| Average retrieval latency (ms) | 11.02 |

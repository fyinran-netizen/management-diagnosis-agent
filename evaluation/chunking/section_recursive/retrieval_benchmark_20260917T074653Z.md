# Retrieval Benchmark Summary

## Benchmark information

- Timestamp (UTC): `2026-09-17T07:46:53Z`
- Cases: `48`
- Top K: `20`
- Case file: `D:\management_diagnosis_agent\evaluation\retrieval\cases\retrieval_cases.json`
- JSON report: `D:\management_diagnosis_agent\evaluation\chunking\section_recursive\retrieval_benchmark_20260917T074653Z.json`

## Retrieval method configurations

| Method | Configuration |
| --- | --- |
| `bm25` | top_k=`20`, ks=`[1, 3, 5, 10, 20]`, metadata_mode=`base`, corpus_dir=`D:\management_diagnosis_agent\data\chunking_strategy_experiments\section_recursive\corpus` |
| `embedding` | top_k=`20`, ks=`[1, 3, 5, 10, 20]`, index_dir=`D:\management_diagnosis_agent\data\chunking_strategy_experiments\section_recursive\vector_index`, embedding_model=`BAAI/bge-small-zh-v1.5` |
| `linear_hybrid` | top_k=`20`, ks=`[1, 3, 5, 10, 20]`, keyword_weight=`0.15`, embedding_weight=`0.85`, candidate_k=`100`, corpus_dir=`D:\management_diagnosis_agent\data\chunking_strategy_experiments\section_recursive\corpus`, index_dir=`D:\management_diagnosis_agent\data\chunking_strategy_experiments\section_recursive\vector_index`, bm25_metadata_mode=`base` |

## Summary

Best values are bolded.

| Method | Hit@1 | Hit@3 | Hit@5 | Recall@5 | Recall@10 | MRR@5 | nDCG@5 | nDCG@10 | Evidence Coverage@5 | Evidence Density@5 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `bm25` | **0.396** | 0.646 | 0.792 | 0.413 | 0.580 | **0.539** | 0.367 | 0.444 | 0.405 | 0.061 |
| `embedding` | 0.250 | 0.562 | 0.646 | 0.365 | 0.566 | 0.413 | 0.320 | 0.408 | 0.363 | 0.057 |
| `linear_hybrid` | 0.333 | **0.750** | **0.833** | **0.514** | **0.688** | 0.532 | **0.431** | **0.510** | **0.504** | **0.079** |

## Chunking diagnostics

| Metric | Value |
| --- | ---: |
| Chunk count | 163 |
| Mean length | 694.44 |
| Median length | 774 |
| P95 length | 888 |
| Min length | 20 |
| Max length | 899 |
| Total chunk chars | 113194 |
| Total overlap chars | 0 |
| Overlap ratio | 0.0000 |
| Embedding index build time (ms) | 18602.10 |
| Average retrieval latency (ms) | 14.59 |

# Retrieval Benchmark Summary

## Benchmark information

- Timestamp (UTC): `2026-09-17T05:43:29Z`
- Cases: `48`
- Top K: `20`
- Case file: `D:\management_diagnosis_agent\evaluation\retrieval\cases\retrieval_cases.json`
- JSON report: `D:\management_diagnosis_agent\evaluation\chunking\section_raw\retrieval_benchmark_20260917T054329Z.json`

## Retrieval method configurations

| Method | Configuration |
| --- | --- |
| `bm25` | top_k=`20`, ks=`[1, 3, 5, 10, 20]`, metadata_mode=`base`, corpus_dir=`D:\management_diagnosis_agent\data\chunking_strategy_experiments\section_raw\corpus` |
| `embedding` | top_k=`20`, ks=`[1, 3, 5, 10, 20]`, index_dir=`D:\management_diagnosis_agent\data\chunking_strategy_experiments\section_raw\vector_index`, embedding_model=`BAAI/bge-small-zh-v1.5` |
| `linear_hybrid` | top_k=`20`, ks=`[1, 3, 5, 10, 20]`, keyword_weight=`0.15`, embedding_weight=`0.85`, candidate_k=`100`, corpus_dir=`D:\management_diagnosis_agent\data\chunking_strategy_experiments\section_raw\corpus`, index_dir=`D:\management_diagnosis_agent\data\chunking_strategy_experiments\section_raw\vector_index`, bm25_metadata_mode=`base` |

## Summary

Best values are bolded.

| Method | Hit@1 | Hit@3 | Hit@5 | Recall@5 | Recall@10 | MRR@5 | nDCG@5 | nDCG@10 | Evidence Coverage@5 | Evidence Density@5 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `bm25` | 0.542 | 0.750 | **0.917** | 0.649 | 0.840 | 0.677 | 0.442 | 0.528 | 0.655 | 0.029 |
| `embedding` | 0.354 | 0.688 | 0.833 | 0.615 | 0.819 | 0.531 | 0.398 | 0.481 | 0.564 | 0.037 |
| `linear_hybrid` | **0.604** | **0.896** | 0.917 | **0.757** | **0.889** | **0.731** | **0.540** | **0.594** | **0.746** | **0.043** |

## Chunking diagnostics

| Metric | Value |
| --- | ---: |
| Chunk count | 62 |
| Mean length | 1827.48 |
| Median length | 1679.00 |
| P95 length | 4231 |
| Min length | 341 |
| Max length | 5128 |
| Total chunk chars | 113304 |
| Total overlap chars | 0 |
| Overlap ratio | 0.0000 |
| Embedding index build time (ms) | 8185.80 |
| Average retrieval latency (ms) | 9.31 |

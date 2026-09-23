# Retrieval Benchmark Summary

## Benchmark information

- Timestamp (UTC): `2026-09-17T10:40:15Z`
- Cases: `48`
- Top K: `20`
- Case file: `D:\management_diagnosis_agent\evaluation\retrieval\cases\retrieval_cases.json`
- JSON report: `D:\management_diagnosis_agent\evaluation\chunking\section_based_no_overlap\retrieval_benchmark_20260917T104015Z.json`

## Retrieval method configurations

| Method | Configuration |
| --- | --- |
| `bm25` | top_k=`20`, ks=`[1, 3, 5, 10, 20]`, metadata_mode=`base`, corpus_dir=`D:\management_diagnosis_agent\data\chunking_strategy_experiments\section_based_no_overlap\corpus` |
| `embedding` | top_k=`20`, ks=`[1, 3, 5, 10, 20]`, index_dir=`D:\management_diagnosis_agent\data\chunking_strategy_experiments\section_based_no_overlap\vector_index`, embedding_model=`BAAI/bge-small-zh-v1.5` |
| `linear_hybrid` | top_k=`20`, ks=`[1, 3, 5, 10, 20]`, keyword_weight=`0.15`, embedding_weight=`0.85`, candidate_k=`100`, corpus_dir=`D:\management_diagnosis_agent\data\chunking_strategy_experiments\section_based_no_overlap\corpus`, index_dir=`D:\management_diagnosis_agent\data\chunking_strategy_experiments\section_based_no_overlap\vector_index`, bm25_metadata_mode=`base` |

## Summary

Best values are bolded.

| Method | Hit@1 | Hit@3 | Hit@5 | Recall@5 | Recall@10 | MRR@5 | nDCG@5 | nDCG@10 | Evidence Coverage@5 | Evidence Density@5 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `bm25` | **0.396** | 0.646 | 0.792 | 0.413 | 0.587 | **0.543** | 0.369 | 0.449 | 0.405 | 0.061 |
| `embedding` | 0.229 | 0.562 | 0.667 | 0.372 | 0.552 | 0.403 | 0.315 | 0.397 | 0.371 | 0.055 |
| `linear_hybrid` | 0.312 | **0.729** | **0.833** | **0.514** | **0.688** | 0.517 | **0.425** | **0.504** | **0.499** | **0.076** |

## Chunking diagnostics

| Metric | Value |
| --- | ---: |
| Chunk count | 162 |
| Mean length | 698.19 |
| Median length | 774.00 |
| P95 length | 889 |
| Min length | 20 |
| Max length | 1189 |
| Total chunk chars | 113106 |
| Total overlap chars | 0 |
| Overlap ratio | 0.0000 |
| Embedding index build time (ms) | 21155.43 |
| Average retrieval latency (ms) | 15.23 |

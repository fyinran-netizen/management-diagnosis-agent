# Retrieval Benchmark Summary

## Benchmark information

- Timestamp (UTC): `2026-09-17T10:41:00Z`
- Cases: `48`
- Top K: `20`
- Case file: `D:\management_diagnosis_agent\evaluation\retrieval\cases\retrieval_cases.json`
- JSON report: `D:\management_diagnosis_agent\evaluation\chunking\section_recursive_overlap\retrieval_benchmark_20260917T104100Z.json`

## Retrieval method configurations

| Method | Configuration |
| --- | --- |
| `bm25` | top_k=`20`, ks=`[1, 3, 5, 10, 20]`, metadata_mode=`base`, corpus_dir=`D:\management_diagnosis_agent\data\chunking_strategy_experiments\section_recursive_overlap\corpus` |
| `embedding` | top_k=`20`, ks=`[1, 3, 5, 10, 20]`, index_dir=`D:\management_diagnosis_agent\data\chunking_strategy_experiments\section_recursive_overlap\vector_index`, embedding_model=`BAAI/bge-small-zh-v1.5` |
| `linear_hybrid` | top_k=`20`, ks=`[1, 3, 5, 10, 20]`, keyword_weight=`0.15`, embedding_weight=`0.85`, candidate_k=`100`, corpus_dir=`D:\management_diagnosis_agent\data\chunking_strategy_experiments\section_recursive_overlap\corpus`, index_dir=`D:\management_diagnosis_agent\data\chunking_strategy_experiments\section_recursive_overlap\vector_index`, bm25_metadata_mode=`base` |

## Summary

Best values are bolded.

| Method | Hit@1 | Hit@3 | Hit@5 | Recall@5 | Recall@10 | MRR@5 | nDCG@5 | nDCG@10 | Evidence Coverage@5 | Evidence Density@5 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `bm25` | 0.375 | 0.625 | 0.750 | 0.413 | 0.639 | 0.515 | 0.362 | 0.456 | 0.375 | 0.049 |
| `embedding` | 0.292 | 0.604 | 0.688 | 0.441 | 0.646 | 0.453 | 0.367 | 0.455 | 0.421 | 0.060 |
| `linear_hybrid` | **0.458** | **0.750** | **0.833** | **0.549** | **0.726** | **0.602** | **0.471** | **0.549** | **0.512** | **0.074** |

## Chunking diagnostics

| Metric | Value |
| --- | ---: |
| Chunk count | 163 |
| Mean length | 807.20 |
| Median length | 862 |
| P95 length | 1063 |
| Min length | 202 |
| Max length | 1077 |
| Total chunk chars | 131574 |
| Total overlap chars | 18178 |
| Overlap ratio | 0.1382 |
| Embedding index build time (ms) | 22623.96 |
| Average retrieval latency (ms) | 14.54 |

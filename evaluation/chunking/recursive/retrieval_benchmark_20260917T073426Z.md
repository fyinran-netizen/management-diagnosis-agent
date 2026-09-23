# Retrieval Benchmark Summary

## Benchmark information

- Timestamp (UTC): `2026-09-17T07:34:26Z`
- Cases: `48`
- Top K: `20`
- Case file: `D:\management_diagnosis_agent\evaluation\retrieval\cases\retrieval_cases.json`
- JSON report: `D:\management_diagnosis_agent\evaluation\chunking\recursive\retrieval_benchmark_20260917T073426Z.json`

## Retrieval method configurations

| Method | Configuration |
| --- | --- |
| `bm25` | top_k=`20`, ks=`[1, 3, 5, 10, 20]`, metadata_mode=`base`, corpus_dir=`D:\management_diagnosis_agent\data\chunking_strategy_experiments\recursive\corpus` |
| `embedding` | top_k=`20`, ks=`[1, 3, 5, 10, 20]`, index_dir=`D:\management_diagnosis_agent\data\chunking_strategy_experiments\recursive\vector_index`, embedding_model=`BAAI/bge-small-zh-v1.5` |
| `linear_hybrid` | top_k=`20`, ks=`[1, 3, 5, 10, 20]`, keyword_weight=`0.15`, embedding_weight=`0.85`, candidate_k=`100`, corpus_dir=`D:\management_diagnosis_agent\data\chunking_strategy_experiments\recursive\corpus`, index_dir=`D:\management_diagnosis_agent\data\chunking_strategy_experiments\recursive\vector_index`, bm25_metadata_mode=`base` |

## Summary

Best values are bolded.

| Method | Hit@1 | Hit@3 | Hit@5 | Recall@5 | Recall@10 | MRR@5 | nDCG@5 | nDCG@10 | Evidence Coverage@5 | Evidence Density@5 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `bm25` | **0.333** | 0.604 | 0.708 | 0.351 | 0.549 | 0.482 | 0.317 | 0.404 | 0.323 | 0.048 |
| `embedding` | 0.312 | 0.542 | 0.583 | 0.333 | 0.521 | 0.423 | 0.298 | 0.383 | 0.319 | 0.051 |
| `linear_hybrid` | 0.312 | **0.688** | **0.833** | **0.462** | **0.635** | **0.511** | **0.382** | **0.462** | **0.431** | **0.069** |

## Chunking diagnostics

| Metric | Value |
| --- | ---: |
| Chunk count | 149 |
| Mean length | 799.36 |
| Median length | 824 |
| P95 length | 888 |
| Min length | 406 |
| Max length | 897 |
| Total chunk chars | 119104 |
| Total overlap chars | 0 |
| Overlap ratio | 0.0000 |
| Embedding index build time (ms) | 20202.67 |
| Average retrieval latency (ms) | 14.98 |

# Retrieval Benchmark Summary

## Benchmark information

- Timestamp (UTC): `2026-09-17T11:43:42Z`
- Cases: `48`
- Top K: `20`
- Case file: `D:\management_diagnosis_agent\evaluation\retrieval\cases\retrieval_cases.json`
- JSON report: `D:\management_diagnosis_agent\evaluation\chunking\section_semantic\retrieval_benchmark_20260917T114342Z.json`

## Retrieval method configurations

| Method | Configuration |
| --- | --- |
| `bm25` | top_k=`20`, ks=`[1, 3, 5, 10, 20]`, metadata_mode=`base`, corpus_dir=`D:\management_diagnosis_agent\data\chunking_strategy_experiments\section_semantic\corpus` |
| `embedding` | top_k=`20`, ks=`[1, 3, 5, 10, 20]`, index_dir=`D:\management_diagnosis_agent\data\chunking_strategy_experiments\section_semantic\vector_index`, embedding_model=`BAAI/bge-small-zh-v1.5` |
| `linear_hybrid` | top_k=`20`, ks=`[1, 3, 5, 10, 20]`, keyword_weight=`0.15`, embedding_weight=`0.85`, candidate_k=`100`, corpus_dir=`D:\management_diagnosis_agent\data\chunking_strategy_experiments\section_semantic\corpus`, index_dir=`D:\management_diagnosis_agent\data\chunking_strategy_experiments\section_semantic\vector_index`, bm25_metadata_mode=`base` |

## Summary

Best values are bolded.

| Method | Hit@1 | Hit@3 | Hit@5 | Recall@5 | Recall@10 | MRR@5 | nDCG@5 | nDCG@10 | Evidence Coverage@5 | Evidence Density@5 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `bm25` | 0.250 | 0.583 | 0.667 | 0.319 | 0.500 | 0.414 | 0.283 | 0.362 | 0.274 | 0.079 |
| `embedding` | 0.167 | 0.458 | 0.667 | 0.302 | 0.486 | 0.348 | 0.248 | 0.326 | 0.262 | 0.081 |
| `linear_hybrid` | **0.354** | **0.604** | **0.729** | **0.389** | **0.583** | **0.490** | **0.350** | **0.435** | **0.335** | **0.098** |

## Chunking diagnostics

| Metric | Value |
| --- | ---: |
| Chunk count | 302 |
| Mean length | 387.72 |
| Median length | 352.00 |
| P95 length | 614 |
| Min length | 300 |
| Max length | 845 |
| Total chunk chars | 117090 |
| Total overlap chars | 0 |
| Overlap ratio | 0.0000 |
| Embedding index build time (ms) | 14447.60 |
| Average retrieval latency (ms) | 70.63 |


## Chunking strategy configuration

| Parameter | Value |
| --- | --- |
| embedding_model | BAAI/bge-small-zh-v1.5 |
| sentence_splitter | regex_terminal_punctuation |
| min_chars | 300 |
| target_chars | 900 |
| max_chars | 1200 |
| breakpoint_algorithm | adjacent_sentence_cosine_similarity |
| breakpoint_similarity_threshold | 0.55 |
| breakpoint_rule | similarity <= threshold |
| overlap_chars | 0 |
| cross_section | False |

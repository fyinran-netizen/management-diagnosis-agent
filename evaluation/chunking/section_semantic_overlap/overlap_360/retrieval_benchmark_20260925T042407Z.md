# Retrieval Benchmark Summary

## Benchmark information

- Timestamp (UTC): `2026-09-25T04:24:07Z`
- Cases: `48`
- Top K: `20`
- Case file: `D:\management_diagnosis_agent\evaluation\retrieval\cases\retrieval_cases.json`
- JSON report: `D:\management_diagnosis_agent\evaluation\chunking\section_semantic_overlap\overlap_360\retrieval_benchmark_20260925T042407Z.json`

## Retrieval method configurations

| Method | Configuration |
| --- | --- |
| `bm25` | top_k=`20`, ks=`[1, 3, 5, 10, 20]`, metadata_mode=`base`, corpus_dir=`D:\management_diagnosis_agent\data\chunking_strategy_experiments\section_semantic_overlap\overlap_360\corpus` |
| `embedding` | top_k=`20`, ks=`[1, 3, 5, 10, 20]`, index_dir=`D:\management_diagnosis_agent\data\chunking_strategy_experiments\section_semantic_overlap\overlap_360\vector_index`, embedding_model=`BAAI/bge-small-zh-v1.5` |
| `linear_hybrid` | top_k=`20`, ks=`[1, 3, 5, 10, 20]`, keyword_weight=`0.15`, embedding_weight=`0.85`, candidate_k=`100`, corpus_dir=`D:\management_diagnosis_agent\data\chunking_strategy_experiments\section_semantic_overlap\overlap_360\corpus`, index_dir=`D:\management_diagnosis_agent\data\chunking_strategy_experiments\section_semantic_overlap\overlap_360\vector_index`, bm25_metadata_mode=`base` |

## Summary

Best values are bolded.

| Method | Hit@1 | Hit@3 | Hit@5 | Recall@5 | Recall@10 | MRR@5 | nDCG@5 | nDCG@10 | Evidence Coverage@5 | Evidence Density@5 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `bm25` | 0.396 | 0.708 | 0.833 | 0.462 | 0.642 | 0.555 | 0.402 | 0.476 | 0.410 | 0.051 |
| `embedding` | 0.354 | 0.604 | 0.688 | 0.399 | 0.656 | 0.482 | 0.358 | 0.471 | 0.403 | 0.055 |
| `linear_hybrid` | **0.417** | **0.750** | **0.854** | **0.562** | **0.740** | **0.594** | **0.475** | **0.549** | **0.553** | **0.078** |

## Chunking diagnostics

| Metric | Value |
| --- | ---: |
| Chunk count | 142 |
| Mean length | 1015.51 |
| Median length | 1004.00 |
| P95 length | 1363 |
| Min length | 353 |
| Max length | 1416 |
| Total chunk chars | 144203 |
| Total overlap chars | 26633 |
| Overlap ratio | 0.1847 |
| Embedding index build time (ms) | 12234.92 |
| Average retrieval latency (ms) | 12.43 |


## Chunking strategy configuration

| Parameter | Value |
| --- | --- |
| requested_overlap_chars | 360 |
| embedding_model | BAAI/bge-small-zh-v1.5 |
| sentence_splitter | regex_terminal_punctuation |
| min_chars | 300 |
| target_chars | 900 |
| max_chars | 1200 |
| breakpoint_algorithm | adjacent_sentence_cosine_similarity |
| breakpoint_similarity_threshold | 0.55 |
| breakpoint_rule | choose the strongest eligible breakpoint near target; threshold gates candidates |
| semantic_breakpoint_start_chars | 600 |
| target_selection_window_chars | 150 |
| overlap_chars | 360 |
| cross_section | False |
| overlap_policy | suffix of complete sentences; approximate length allowed |

# Retrieval Benchmark Summary

## Benchmark information

- Timestamp (UTC): `2026-09-25T04:23:20Z`
- Cases: `48`
- Top K: `20`
- Case file: `D:\management_diagnosis_agent\evaluation\retrieval\cases\retrieval_cases.json`
- JSON report: `D:\management_diagnosis_agent\evaluation\chunking\section_semantic_overlap\overlap_270\retrieval_benchmark_20260925T042320Z.json`

## Retrieval method configurations

| Method | Configuration |
| --- | --- |
| `bm25` | top_k=`20`, ks=`[1, 3, 5, 10, 20]`, metadata_mode=`base`, corpus_dir=`D:\management_diagnosis_agent\data\chunking_strategy_experiments\section_semantic_overlap\overlap_270\corpus` |
| `embedding` | top_k=`20`, ks=`[1, 3, 5, 10, 20]`, index_dir=`D:\management_diagnosis_agent\data\chunking_strategy_experiments\section_semantic_overlap\overlap_270\vector_index`, embedding_model=`BAAI/bge-small-zh-v1.5` |
| `linear_hybrid` | top_k=`20`, ks=`[1, 3, 5, 10, 20]`, keyword_weight=`0.15`, embedding_weight=`0.85`, candidate_k=`100`, corpus_dir=`D:\management_diagnosis_agent\data\chunking_strategy_experiments\section_semantic_overlap\overlap_270\corpus`, index_dir=`D:\management_diagnosis_agent\data\chunking_strategy_experiments\section_semantic_overlap\overlap_270\vector_index`, bm25_metadata_mode=`base` |

## Summary

Best values are bolded.

| Method | Hit@1 | Hit@3 | Hit@5 | Recall@5 | Recall@10 | MRR@5 | nDCG@5 | nDCG@10 | Evidence Coverage@5 | Evidence Density@5 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `bm25` | 0.417 | 0.667 | 0.792 | 0.424 | 0.639 | 0.552 | 0.380 | 0.470 | 0.378 | 0.045 |
| `embedding` | 0.333 | 0.646 | 0.750 | 0.469 | 0.674 | 0.496 | 0.388 | 0.480 | 0.457 | 0.066 |
| `linear_hybrid` | **0.500** | **0.771** | **0.854** | **0.597** | **0.747** | **0.644** | **0.505** | **0.573** | **0.553** | **0.075** |

## Chunking diagnostics

| Metric | Value |
| --- | ---: |
| Chunk count | 142 |
| Mean length | 965.73 |
| Median length | 988.00 |
| P95 length | 1272 |
| Min length | 353 |
| Max length | 1338 |
| Total chunk chars | 137133 |
| Total overlap chars | 19563 |
| Overlap ratio | 0.1427 |
| Embedding index build time (ms) | 12065.29 |
| Average retrieval latency (ms) | 12.19 |


## Chunking strategy configuration

| Parameter | Value |
| --- | --- |
| requested_overlap_chars | 270 |
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
| overlap_chars | 270 |
| cross_section | False |
| overlap_policy | suffix of complete sentences; approximate length allowed |

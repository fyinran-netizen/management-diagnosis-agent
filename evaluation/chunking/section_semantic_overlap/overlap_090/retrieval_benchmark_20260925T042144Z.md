# Retrieval Benchmark Summary

## Benchmark information

- Timestamp (UTC): `2026-09-25T04:21:44Z`
- Cases: `48`
- Top K: `20`
- Case file: `D:\management_diagnosis_agent\evaluation\retrieval\cases\retrieval_cases.json`
- JSON report: `D:\management_diagnosis_agent\evaluation\chunking\section_semantic_overlap\overlap_090\retrieval_benchmark_20260925T042144Z.json`

## Retrieval method configurations

| Method | Configuration |
| --- | --- |
| `bm25` | top_k=`20`, ks=`[1, 3, 5, 10, 20]`, metadata_mode=`base`, corpus_dir=`D:\management_diagnosis_agent\data\chunking_strategy_experiments\section_semantic_overlap\overlap_090\corpus` |
| `embedding` | top_k=`20`, ks=`[1, 3, 5, 10, 20]`, index_dir=`D:\management_diagnosis_agent\data\chunking_strategy_experiments\section_semantic_overlap\overlap_090\vector_index`, embedding_model=`BAAI/bge-small-zh-v1.5` |
| `linear_hybrid` | top_k=`20`, ks=`[1, 3, 5, 10, 20]`, keyword_weight=`0.15`, embedding_weight=`0.85`, candidate_k=`100`, corpus_dir=`D:\management_diagnosis_agent\data\chunking_strategy_experiments\section_semantic_overlap\overlap_090\corpus`, index_dir=`D:\management_diagnosis_agent\data\chunking_strategy_experiments\section_semantic_overlap\overlap_090\vector_index`, bm25_metadata_mode=`base` |

## Summary

Best values are bolded.

| Method | Hit@1 | Hit@3 | Hit@5 | Recall@5 | Recall@10 | MRR@5 | nDCG@5 | nDCG@10 | Evidence Coverage@5 | Evidence Density@5 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `bm25` | 0.354 | **0.688** | 0.750 | 0.392 | 0.590 | 0.523 | 0.353 | 0.441 | 0.360 | 0.045 |
| `embedding` | 0.250 | 0.604 | 0.708 | 0.399 | 0.635 | 0.431 | 0.322 | 0.430 | 0.405 | 0.057 |
| `linear_hybrid` | **0.417** | 0.688 | **0.854** | **0.556** | **0.729** | **0.576** | **0.457** | **0.536** | **0.548** | **0.075** |

## Chunking diagnostics

| Metric | Value |
| --- | ---: |
| Chunk count | 142 |
| Mean length | 868.69 |
| Median length | 903.00 |
| P95 length | 1111 |
| Min length | 313 |
| Max length | 1140 |
| Total chunk chars | 123354 |
| Total overlap chars | 5784 |
| Overlap ratio | 0.0469 |
| Embedding index build time (ms) | 11016.48 |
| Average retrieval latency (ms) | 11.38 |


## Chunking strategy configuration

| Parameter | Value |
| --- | --- |
| requested_overlap_chars | 90 |
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
| overlap_chars | 90 |
| cross_section | False |
| overlap_policy | suffix of complete sentences; approximate length allowed |

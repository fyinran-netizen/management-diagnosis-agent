# Retrieval Benchmark Summary

## Benchmark information

- Timestamp (UTC): `2026-09-17T11:51:10Z`
- Cases: `48`
- Top K: `20`
- Case file: `D:\management_diagnosis_agent\evaluation\retrieval\cases\retrieval_cases.json`
- JSON report: `D:\management_diagnosis_agent\evaluation\chunking\section_semantic_overlap\retrieval_benchmark_20260917T115110Z.json`

## Retrieval method configurations

| Method | Configuration |
| --- | --- |
| `bm25` | top_k=`20`, ks=`[1, 3, 5, 10, 20]`, metadata_mode=`base`, corpus_dir=`D:\management_diagnosis_agent\data\chunking_strategy_experiments\section_semantic_overlap\corpus` |
| `embedding` | top_k=`20`, ks=`[1, 3, 5, 10, 20]`, index_dir=`D:\management_diagnosis_agent\data\chunking_strategy_experiments\section_semantic_overlap\vector_index`, embedding_model=`BAAI/bge-small-zh-v1.5` |
| `linear_hybrid` | top_k=`20`, ks=`[1, 3, 5, 10, 20]`, keyword_weight=`0.15`, embedding_weight=`0.85`, candidate_k=`100`, corpus_dir=`D:\management_diagnosis_agent\data\chunking_strategy_experiments\section_semantic_overlap\corpus`, index_dir=`D:\management_diagnosis_agent\data\chunking_strategy_experiments\section_semantic_overlap\vector_index`, bm25_metadata_mode=`base` |

## Summary

Best values are bolded.

| Method | Hit@1 | Hit@3 | Hit@5 | Recall@5 | Recall@10 | MRR@5 | nDCG@5 | nDCG@10 | Evidence Coverage@5 | Evidence Density@5 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `bm25` | 0.417 | 0.667 | 0.771 | 0.417 | 0.618 | 0.557 | 0.382 | 0.467 | 0.367 | 0.045 |
| `embedding` | 0.333 | 0.604 | 0.750 | 0.462 | 0.635 | 0.486 | 0.384 | 0.461 | 0.443 | 0.063 |
| `linear_hybrid` | **0.479** | **0.750** | **0.875** | **0.576** | **0.747** | **0.626** | **0.481** | **0.554** | **0.558** | **0.077** |

## Chunking diagnostics

| Metric | Value |
| --- | ---: |
| Chunk count | 142 |
| Mean length | 914.85 |
| Median length | 950.00 |
| P95 length | 1188 |
| Min length | 353 |
| Max length | 1224 |
| Total chunk chars | 129909 |
| Total overlap chars | 12339 |
| Overlap ratio | 0.0950 |
| Embedding index build time (ms) | 10506.05 |
| Average retrieval latency (ms) | 10.57 |


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
| breakpoint_rule | choose the strongest eligible breakpoint near target; threshold gates candidates |
| semantic_breakpoint_start_chars | 600 |
| target_selection_window_chars | 150 |
| overlap_chars | 180 |
| cross_section | False |
| overlap_policy | suffix of complete sentences; approximate length allowed |

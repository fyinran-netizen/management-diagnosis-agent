# Retrieval Benchmark Summary

## Benchmark information

- Timestamp (UTC): `2026-09-17T11:47:29Z`
- Cases: `48`
- Top K: `20`
- Case file: `D:\management_diagnosis_agent\evaluation\retrieval\cases\retrieval_cases.json`
- JSON report: `D:\management_diagnosis_agent\evaluation\chunking\section_semantic\retrieval_benchmark_20260917T114729Z.json`

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
| `bm25` | 0.438 | 0.688 | 0.792 | 0.399 | 0.597 | 0.573 | 0.369 | 0.456 | 0.371 | 0.049 |
| `embedding` | 0.292 | 0.625 | 0.729 | 0.406 | 0.656 | 0.468 | 0.349 | 0.458 | 0.412 | 0.057 |
| `linear_hybrid` | **0.458** | **0.771** | **0.833** | **0.562** | **0.757** | **0.621** | **0.485** | **0.572** | **0.537** | **0.075** |

## Chunking diagnostics

| Metric | Value |
| --- | ---: |
| Chunk count | 142 |
| Mean length | 826.83 |
| Median length | 880.00 |
| P95 length | 1035 |
| Min length | 229 |
| Max length | 1140 |
| Total chunk chars | 117410 |
| Total overlap chars | 0 |
| Overlap ratio | 0.0000 |
| Embedding index build time (ms) | 10772.16 |
| Average retrieval latency (ms) | 10.29 |


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
| overlap_chars | 0 |
| cross_section | False |

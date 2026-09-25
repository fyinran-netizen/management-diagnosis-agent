# Retrieval Benchmark Summary

## Benchmark information

- Timestamp (UTC): `2026-09-25T06:42:13Z`
- Cases: `48`
- Top K: `20`
- Case file: `D:\management_diagnosis_agent\evaluation\retrieval\cases\retrieval_cases.json`
- JSON report: `D:\management_diagnosis_agent\evaluation\retrieval\reports\retrieval_benchmark_20260925T064213Z.json`

## Retrieval method configurations

| Method | Configuration |
| --- | --- |
| `bm25` | top_k=`20`, ks=`[1, 3, 5, 10, 20]`, metadata_mode=`base`, corpus_dir=`data\chunking_strategy_experiments\section_semantic_overlap\overlap_180\corpus` |
| `bm25_semantic_metadata` | top_k=`20`, ks=`[1, 3, 5, 10, 20]`, metadata_mode=`unweighted`, corpus_dir=`data\chunking_strategy_experiments\section_semantic_overlap\overlap_180\corpus` |

## Summary

Best values are bolded.

| Method | Hit@1 | Hit@3 | Hit@5 | Recall@5 | Recall@10 | MRR@5 | nDCG@5 | nDCG@10 | Evidence Coverage@5 | Evidence Density@5 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `bm25` | 0.417 | 0.667 | 0.771 | 0.417 | 0.618 | 0.557 | 0.382 | 0.467 | 0.367 | 0.045 |
| `bm25_semantic_metadata` | **0.646** | **0.771** | **0.833** | **0.497** | **0.642** | **0.711** | **0.468** | **0.531** | **0.439** | **0.057** |

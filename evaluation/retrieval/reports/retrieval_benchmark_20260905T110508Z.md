# Retrieval Benchmark Summary

## Benchmark information

- Timestamp (UTC): `2026-09-05T11:05:08Z`
- Cases: `48`
- Top K: `20`
- Case file: `D:\management_diagnosis_agent\evaluation\retrieval\cases\retrieval_cases.json`
- JSON report: `D:\management_diagnosis_agent\evaluation\retrieval\reports\retrieval_benchmark_20260905T110508Z.json`

## Retrieval method configurations

| Method | Configuration |
| --- | --- |
| `keyword` | top_k=`20`, ks=`[1, 3, 5, 10, 20]`, retriever=`keyword baseline` |
| `bm25` | top_k=`20`, ks=`[1, 3, 5, 10, 20]`, metadata_mode=`base` |
| `bm25_semantic_metadata` | top_k=`20`, ks=`[1, 3, 5, 10, 20]`, metadata_mode=`unweighted` |
| `embedding` | top_k=`20`, ks=`[1, 3, 5, 10, 20]`, index_dir=`D:\management_diagnosis_agent\data\vector_index\base`, embedding_model=`BAAI/bge-small-zh-v1.5` |
| `metadata_embedding` | top_k=`20`, ks=`[1, 3, 5, 10, 20]`, index_dir=`D:\management_diagnosis_agent\data\vector_index\semantic_metadata_unweighted`, embedding_model=`BAAI/bge-small-zh-v1.5` |
| `linear_hybrid` | top_k=`20`, ks=`[1, 3, 5, 10, 20]`, keyword_weight=`0.15`, embedding_weight=`0.85`, candidate_k=`100` |
| `rrf_hybrid` | top_k=`20`, ks=`[1, 3, 5, 10, 20]`, rrf_k=`60.0`, candidate_k=`100` |

## Summary

Best values are bolded.

| Method | Hit@1 | Hit@3 | Hit@5 | Recall@5 | Recall@10 | MRR@5 | nDCG@5 | nDCG@10 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `keyword` | 0.104 | 0.354 | 0.417 | 0.215 | 0.368 | 0.226 | 0.175 | 0.243 |
| `bm25` | 0.312 | 0.625 | 0.646 | 0.326 | 0.542 | 0.443 | 0.311 | 0.409 |
| `bm25_semantic_metadata` | **0.479** | 0.646 | 0.708 | 0.396 | 0.521 | 0.568 | 0.394 | 0.450 |
| `embedding` | 0.146 | 0.562 | 0.729 | 0.396 | 0.569 | 0.360 | 0.311 | 0.388 |
| `metadata_embedding` | 0.146 | 0.604 | 0.708 | 0.389 | 0.562 | 0.359 | 0.308 | 0.386 |
| `linear_hybrid` | 0.375 | **0.750** | **0.875** | **0.521** | **0.667** | 0.567 | **0.457** | **0.522** |
| `rrf_hybrid` | 0.458 | 0.667 | 0.833 | 0.479 | 0.632 | **0.586** | 0.444 | 0.514 |


## 一些结论
1. naive keyword 明显弱于 BM25
2. semantic metadata 显著增强 BM25
3. metadata embedding 当前没有带来提升
4. hybrid 明显优于单一 sparse/dense retrieval
5. linear hybrid 在 Top-K recall / ranking 上最好
6. RRF 在 MRR 上略有优势
7. 当前最佳 linear hybrid 是 metadata-enhanced BM25 + base embedding 的线性融合
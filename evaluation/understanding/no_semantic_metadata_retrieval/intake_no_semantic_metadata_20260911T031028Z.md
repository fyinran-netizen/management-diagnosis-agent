# Intake Strategy × Retrieval (No Semantic Metadata)

## Benchmark information

- Timestamp (UTC): `2026-09-11T03:10:28Z`
- Cases: `48`
- Top K: `20`
- Case file (reused): `D:\management_diagnosis_agent\evaluation\retrieval\cases\retrieval_cases.json`
- JSON report: `D:\management_diagnosis_agent\evaluation\understanding\no_semantic_metadata_retrieval\intake_no_semantic_metadata_20260911T031028Z.json`
- Semantic metadata: `false` for every retriever configuration.
- Metrics and case set are reused from `scripts.run_retrieval_benchmark`.

## `bm25`

Configuration: `retriever=bm25`, `top_k=20`, `ks=[1, 3, 5, 10, 20]`, `semantic_metadata=False`, `metadata_mode=base`

| Intake strategy | Hit@1 | Hit@3 | Hit@5 | Recall@5 | Recall@10 | MRR@5 | nDCG@5 | nDCG@10 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Raw | 0.312 | 0.625 | 0.646 | 0.326 | 0.542 | 0.443 | 0.311 | 0.409 |
| Rule-based | 0.271 | 0.583 | 0.708 | 0.326 | 0.521 | 0.426 | 0.293 | 0.379 |
| Rewrite | 0.312 | 0.625 | 0.646 | 0.326 | 0.542 | 0.443 | 0.311 | 0.409 |
| Rule-based vs Raw delta | -0.042 | -0.042 | +0.062 | +0.000 | -0.021 | -0.016 | -0.017 | -0.029 |
| Rewrite vs Raw delta | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |

## `embedding`

Configuration: `retriever=embedding`, `top_k=20`, `ks=[1, 3, 5, 10, 20]`, `semantic_metadata=False`, `index_dir=D:\management_diagnosis_agent\data\vector_index\base`

| Intake strategy | Hit@1 | Hit@3 | Hit@5 | Recall@5 | Recall@10 | MRR@5 | nDCG@5 | nDCG@10 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Raw | 0.146 | 0.562 | 0.729 | 0.396 | 0.569 | 0.360 | 0.311 | 0.388 |
| Rule-based | 0.188 | 0.375 | 0.562 | 0.292 | 0.500 | 0.322 | 0.248 | 0.344 |
| Rewrite | 0.146 | 0.562 | 0.729 | 0.396 | 0.569 | 0.360 | 0.311 | 0.388 |
| Rule-based vs Raw delta | +0.042 | -0.188 | -0.167 | -0.104 | -0.069 | -0.039 | -0.064 | -0.044 |
| Rewrite vs Raw delta | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |

## `hybrid_linear`

Configuration: `retriever=hybrid_linear`, `top_k=20`, `ks=[1, 3, 5, 10, 20]`, `semantic_metadata=False`, `bm25_metadata_mode=base`, `embedding_index_dir=D:\management_diagnosis_agent\data\vector_index\base`, `implementation=app.tools.retrieval.retrievers.hybrid_linear.hybrid_retrieve`

| Intake strategy | Hit@1 | Hit@3 | Hit@5 | Recall@5 | Recall@10 | MRR@5 | nDCG@5 | nDCG@10 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Raw | 0.292 | 0.750 | 0.854 | 0.493 | 0.632 | 0.518 | 0.422 | 0.485 |
| Rule-based | 0.333 | 0.708 | 0.833 | 0.458 | 0.597 | 0.527 | 0.401 | 0.464 |
| Rewrite | 0.292 | 0.750 | 0.854 | 0.493 | 0.632 | 0.518 | 0.422 | 0.485 |
| Rule-based vs Raw delta | +0.042 | -0.042 | -0.021 | -0.035 | -0.035 | +0.008 | -0.022 | -0.021 |
| Rewrite vs Raw delta | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |

## `hybrid_rrf`

Configuration: `retriever=hybrid_rrf`, `top_k=20`, `ks=[1, 3, 5, 10, 20]`, `semantic_metadata=False`, `bm25_metadata_mode=base`, `embedding_index_dir=D:\management_diagnosis_agent\data\vector_index\base`, `implementation=app.tools.retrieval.retrievers.hybrid_rrf.hybrid_retrieve_rrf`

| Intake strategy | Hit@1 | Hit@3 | Hit@5 | Recall@5 | Recall@10 | MRR@5 | nDCG@5 | nDCG@10 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Raw | 0.354 | 0.667 | 0.792 | 0.458 | 0.618 | 0.523 | 0.411 | 0.484 |
| Rule-based | 0.292 | 0.667 | 0.833 | 0.444 | 0.569 | 0.502 | 0.390 | 0.446 |
| Rewrite | 0.354 | 0.667 | 0.792 | 0.458 | 0.618 | 0.523 | 0.411 | 0.484 |
| Rule-based vs Raw delta | -0.062 | +0.000 | +0.042 | -0.014 | -0.049 | -0.022 | -0.021 | -0.038 |
| Rewrite vs Raw delta | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |

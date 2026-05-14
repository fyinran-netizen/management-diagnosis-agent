# Retrieval Experiments

## baseline_linear_035_065

- cases: 16
- top_k: 5
- keyword_weight: 0.35
- embedding_weight: 0.65
- candidate_multiplier: 3
- min_candidates: 10
- notes: Initial linear hybrid fusion with keyword_weight=0.35 and embedding_weight=0.65.

| method | cases | hit@3 | hit@5 | recall@5 | mrr@5 |
| --- | ---: | ---: | ---: | ---: | ---: |
| keyword | 16 | 0.375 | 0.438 | 0.167 | 0.245 |
| embedding | 16 | 0.625 | 0.812 | 0.458 | 0.481 |
| hybrid | 16 | 0.562 | 0.750 | 0.354 | 0.547 |

## linear_025_075_candidates_3x10

- cases: 16
- top_k: 5
- keyword_weight: 0.25
- embedding_weight: 0.75
- candidate_multiplier: 3
- min_candidates: 10
- notes: Baseline showed embedding had stronger hit/recall while hybrid had stronger MRR, so this run shifts weight toward embedding to improve coverage while retaining keyword signal.

| method | cases | hit@3 | hit@5 | recall@5 | mrr@5 |
| --- | ---: | ---: | ---: | ---: | ---: |
| keyword | 16 | 0.375 | 0.438 | 0.167 | 0.245 |
| embedding | 16 | 0.625 | 0.812 | 0.458 | 0.481 |
| hybrid | 16 | 0.562 | 0.750 | 0.354 | 0.578 |

## linear_025_075_candidates_5x25

- cases: 16
- top_k: 5
- keyword_weight: 0.25
- embedding_weight: 0.75
- candidate_multiplier: 5
- min_candidates: 25
- notes: Previous 0.25/0.75 run improved MRR but not hit/recall, so this run keeps the better weight balance and expands the candidate pool to test whether broader candidate coverage improves recall.

| method | cases | hit@3 | hit@5 | recall@5 | mrr@5 |
| --- | ---: | ---: | ---: | ---: | ---: |
| keyword | 16 | 0.375 | 0.438 | 0.167 | 0.245 |
| embedding | 16 | 0.625 | 0.812 | 0.458 | 0.481 |
| hybrid | 16 | 0.562 | 0.812 | 0.438 | 0.577 |

## linear_015_085_candidates_5x25

- cases: 16
- top_k: 5
- keyword_weight: 0.15
- embedding_weight: 0.85
- candidate_multiplier: 5
- min_candidates: 25
- notes: The expanded candidate pool improved hit/recall while preserving MRR. This run further shifts toward embedding to test whether hybrid can match embedding recall without losing too much ranking quality.

| method | cases | hit@3 | hit@5 | recall@5 | mrr@5 |
| --- | ---: | ---: | ---: | ---: | ---: |
| keyword | 16 | 0.375 | 0.438 | 0.167 | 0.245 |
| embedding | 16 | 0.625 | 0.812 | 0.458 | 0.481 |
| hybrid | 16 | 0.562 | 0.812 | 0.438 | 0.588 |

## Selection

`linear_015_085_candidates_5x25` is the current default. It keeps the improved hybrid Hit@5 and Recall@5 from the expanded candidate pool while producing the best MRR@5 among the recorded hybrid runs. This means the retriever preserves broader candidate coverage and ranks the first relevant chunk highest in the current eval set.

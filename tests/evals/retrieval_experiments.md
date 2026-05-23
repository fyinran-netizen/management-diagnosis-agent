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

## rrf_k60_candidates_5x25

- cases: 16
- top_k: 5
- keyword_weight: 0.15
- embedding_weight: 0.85
- candidate_multiplier: 5
- min_candidates: 25
- rrf_k: 60.0
- rrf_candidate_multiplier: 5
- rrf_min_candidates: 25
- notes: Added RRF hybrid retriever and compared it against the existing linear hybrid baseline.

| method | cases | hit@3 | hit@5 | recall@5 | mrr@5 |
| --- | ---: | ---: | ---: | ---: | ---: |
| keyword | 16 | 0.375 | 0.438 | 0.167 | 0.245 |
| embedding | 16 | 0.625 | 0.812 | 0.458 | 0.481 |
| hybrid | 16 | 0.562 | 0.812 | 0.438 | 0.588 |
| hybrid_rrf | 16 | 0.562 | 0.688 | 0.396 | 0.525 |

## rrf_k10_candidates_5x25

- cases: 16
- top_k: 5
- keyword_weight: 0.15
- embedding_weight: 0.85
- candidate_multiplier: 5
- min_candidates: 25
- rrf_k: 10.0
- rrf_candidate_multiplier: 5
- rrf_min_candidates: 25
- notes: RRF sweep with stronger rank emphasis: k=10, candidates=5x25.

| method | cases | hit@3 | hit@5 | recall@5 | mrr@5 |
| --- | ---: | ---: | ---: | ---: | ---: |
| keyword | 16 | 0.375 | 0.438 | 0.167 | 0.245 |
| embedding | 16 | 0.625 | 0.812 | 0.458 | 0.481 |
| hybrid | 16 | 0.562 | 0.812 | 0.438 | 0.588 |
| hybrid_rrf | 16 | 0.562 | 0.625 | 0.375 | 0.516 |

## rrf_k30_candidates_5x25

- cases: 16
- top_k: 5
- keyword_weight: 0.15
- embedding_weight: 0.85
- candidate_multiplier: 5
- min_candidates: 25
- rrf_k: 30.0
- rrf_candidate_multiplier: 5
- rrf_min_candidates: 25
- notes: RRF sweep with moderate rank smoothing: k=30, candidates=5x25.

| method | cases | hit@3 | hit@5 | recall@5 | mrr@5 |
| --- | ---: | ---: | ---: | ---: | ---: |
| keyword | 16 | 0.375 | 0.438 | 0.167 | 0.245 |
| embedding | 16 | 0.625 | 0.812 | 0.458 | 0.481 |
| hybrid | 16 | 0.562 | 0.812 | 0.438 | 0.588 |
| hybrid_rrf | 16 | 0.562 | 0.688 | 0.396 | 0.525 |

## rrf_k60_candidates_3x10

- cases: 16
- top_k: 5
- keyword_weight: 0.15
- embedding_weight: 0.85
- candidate_multiplier: 5
- min_candidates: 25
- rrf_k: 60.0
- rrf_candidate_multiplier: 3
- rrf_min_candidates: 10
- notes: RRF sweep matching the smaller candidate pool used by an earlier linear hybrid experiment.

| method | cases | hit@3 | hit@5 | recall@5 | mrr@5 |
| --- | ---: | ---: | ---: | ---: | ---: |
| keyword | 16 | 0.375 | 0.438 | 0.167 | 0.245 |
| embedding | 16 | 0.625 | 0.812 | 0.458 | 0.481 |
| hybrid | 16 | 0.562 | 0.812 | 0.438 | 0.588 |
| hybrid_rrf | 16 | 0.562 | 0.625 | 0.292 | 0.512 |

## rrf_k60_candidates_10x50

- cases: 16
- top_k: 5
- keyword_weight: 0.15
- embedding_weight: 0.85
- candidate_multiplier: 5
- min_candidates: 25
- rrf_k: 60.0
- rrf_candidate_multiplier: 10
- rrf_min_candidates: 50
- notes: RRF sweep with a broader candidate pool: k=60, candidates=10x50.

| method | cases | hit@3 | hit@5 | recall@5 | mrr@5 |
| --- | ---: | ---: | ---: | ---: | ---: |
| keyword | 16 | 0.375 | 0.438 | 0.167 | 0.245 |
| embedding | 16 | 0.625 | 0.812 | 0.458 | 0.481 |
| hybrid | 16 | 0.562 | 0.812 | 0.438 | 0.588 |
| hybrid_rrf | 16 | 0.625 | 0.688 | 0.396 | 0.533 |

## rrf_k100_candidates_5x25

- cases: 16
- top_k: 5
- keyword_weight: 0.15
- embedding_weight: 0.85
- candidate_multiplier: 5
- min_candidates: 25
- rrf_k: 100.0
- rrf_candidate_multiplier: 5
- rrf_min_candidates: 25
- notes: RRF sweep with weaker top-rank emphasis: k=100, candidates=5x25.

| method | cases | hit@3 | hit@5 | recall@5 | mrr@5 |
| --- | ---: | ---: | ---: | ---: | ---: |
| keyword | 16 | 0.375 | 0.438 | 0.167 | 0.245 |
| embedding | 16 | 0.625 | 0.812 | 0.458 | 0.481 |
| hybrid | 16 | 0.562 | 0.812 | 0.438 | 0.588 |
| hybrid_rrf | 16 | 0.562 | 0.688 | 0.396 | 0.525 |

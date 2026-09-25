# overlap_180 Retrieval Comparison

## Benchmark setup

- Cases: `48`
- Top K: `20`
- Test cases: same as the previous overlap_180 chunking benchmark
- Corpus: `data/chunking_strategy_experiments/section_semantic_overlap/overlap_180/corpus`
- BM25: `metadata_mode=unweighted`, reading the corpus-local `semantic_metadata.jsonl`
- Embedding: existing pure-content vector index; semantic metadata not included
- Linear hybrid: keyword weight `0.15`, embedding weight `0.85`, candidate_k `100`
- New report: `retrieval_benchmark_20260925T050924Z.json`
- Baseline report: `evaluation/chunking/section_semantic_overlap/overlap_180/retrieval_benchmark_20260925T042234Z.json`

## Metrics

Positive delta means the unweighted-metadata run improved over the BM25-base baseline.

| Method | Metric | BM25 base | Unweighted | Delta |
| --- | --- | ---: | ---: | ---: |
| BM25 | Evidence Coverage@5 | 0.367 | 0.354 | -0.012 |
| BM25 | Evidence Density@5 | 0.045 | 0.046 | +0.000 |
| BM25 | Recall@5 | 0.417 | 0.406 | -0.010 |
| BM25 | nDCG@5 | 0.382 | 0.381 | -0.001 |
| BM25 | Hit@5 | 0.771 | 0.750 | -0.021 |
| BM25 | MRR@5 | 0.557 | 0.573 | +0.016 |
| Embedding | Evidence Coverage@5 | 0.443 | 0.443 | +0.000 |
| Embedding | Evidence Density@5 | 0.063 | 0.063 | +0.000 |
| Embedding | Recall@5 | 0.462 | 0.462 | +0.000 |
| Embedding | nDCG@5 | 0.384 | 0.384 | +0.000 |
| Embedding | Hit@5 | 0.750 | 0.750 | +0.000 |
| Embedding | MRR@5 | 0.486 | 0.486 | +0.000 |
| Linear Hybrid | Evidence Coverage@5 | 0.558 | 0.551 | -0.007 |
| Linear Hybrid | Evidence Density@5 | 0.077 | 0.076 | -0.001 |
| Linear Hybrid | Recall@5 | 0.576 | 0.576 | +0.000 |
| Linear Hybrid | nDCG@5 | 0.481 | 0.487 | +0.005 |
| Linear Hybrid | Hit@5 | 0.875 | 0.896 | +0.021 |
| Linear Hybrid | MRR@5 | 0.626 | 0.641 | +0.015 |

## Summary

Adding unweighted semantic metadata to BM25 reduced Hit@5, Recall@5, and Evidence Coverage@5 slightly, while improving MRR and marginally increasing Evidence Density@5. The linear hybrid improved Hit@5, nDCG@5, and MRR, while Evidence Coverage@5 and Evidence Density@5 were slightly lower. Embedding was unchanged, confirming that it used the existing pure-content vector index.

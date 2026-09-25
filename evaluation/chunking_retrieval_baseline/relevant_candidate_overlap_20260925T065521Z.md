# Relevant Candidate Overlap Diagnostic

- Cases: 48
- BM25 metadata mode: `unweighted`
- Embedding: existing pure-content index
- Top-K: 20; Hybrid candidate_k: 100

## Aggregate

| Metric | Total | Average/query |
|---|---:|---:|
| BM25 semantic relevant | 135 | 2.812 |
| BM25 base relevant | 133 | 2.771 |
| Embedding relevant | 136 | 2.833 |
| Semantic ∩ embedding | 109 | 2.271 |
| Semantic added over base | 8 | 0.167 |
| Added chunks in Hybrid Top-5 | 0 | 0.000 |
| Added chunks outside Hybrid Top-5 | 8 | 0.167 |

- Semantic relevant also in embedding rate: **0.807**
- Semantic/embedding relevant Jaccard: **0.673**

## Representative queries

### metrics_004

Query: 客服为了降低平均处理时长而草草结案，数字变漂亮了但投诉和流失上升；应该怎样重看这个指标？

| Added relevant chunk | Embedding rank | Hybrid rank | In Hybrid Top-5 |
|---|---:|---:|---|
| `ch02/s07_chunk_01.md#chunk_1` | — | 17 | No |
| `ch04/s06_chunk_01.md#chunk_1` | — | — | No |

### opportunity_006

Query: 竞争者都在追某个热点，董事会要求马上跟进；如果不追就怕落后，跟进又可能偏离长期方向，如何区分机会判断和跟风？

| Added relevant chunk | Embedding rank | Hybrid rank | In Hybrid Top-5 |
|---|---:|---:|---|
| `ch03/s05_chunk_01.md#chunk_1` | 19 | 6 | No |

### long_term_decision_003

Query: 面对不确定的未来，好的长期决策依靠什么，而不是依靠什么？

| Added relevant chunk | Embedding rank | Hybrid rank | In Hybrid Top-5 |
|---|---:|---:|---|
| `ch07/s02_chunk_01.md#chunk_1` | 6 | 7 | No |

### opportunity_005

Query: 新技术、海外市场和大客户项目同时出现，团队既缺人又缺验证时间；如何筛选机会、识别能力边界，并决定先做哪一个？

| Added relevant chunk | Embedding rank | Hybrid rank | In Hybrid Top-5 |
|---|---:|---:|---|
| `ch03/s06_chunk_02.md#chunk_2` | — | 9 | No |

### long_term_decision_004

Query: 财务预测显示明年需求会下降，团队因此暂停人才培养和技术积累；怎样在看不清远方时仍保留建设未来的能力？

| Added relevant chunk | Embedding rank | Hybrid rank | In Hybrid Top-5 |
|---|---:|---:|---|
| `ch07/s03_chunk_03.md#chunk_3` | 5 | 6 | No |

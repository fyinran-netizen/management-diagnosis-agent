# Reranking benchmark selected-case analysis

- Source report: `2026-09-08T12:08:13Z`
- Report schema: `reranking_benchmark_v1`
- final K: `10`
- Scope: 8 selected cases; only final Top 10 is included.

> 本文由提取脚本根据现有 benchmark JSON 生成；未重新运行 retrieval 或 reranker。

## customer_value_002

### 基本信息和 query

| Field | Value |
|---|---|
| Topic | `customer_value` |
| Query type | `semantic_rewrite` |
| Difficulty | `medium` |
| Query | 产品功能越来越多，但客户觉得没有解决真实痛点，团队应该如何重新创造客户价值？ |

### Expected sources

`ch01/s07_chunk_01.md`, `ch01/s07_chunk_03.md`, `ch01/s07_chunk_04.md`

### 主要 metrics（final Top 10）

| Metric | Baseline | Rerank | Δ (rerank - baseline) |
|---|---:|---:|---:|
| `hit@1` | 1.0000 | 0.0000 | -1.0000 |
| `hit@3` | 1.0000 | 0.0000 | -1.0000 |
| `hit@5` | 1.0000 | 1.0000 | 0.0000 |
| `recall@5` | 0.6667 | 0.3333 | -0.3333 |
| `recall@10` | 0.6667 | 0.3333 | -0.3333 |
| `mrr@5` | 1.0000 | 0.2000 | -0.8000 |
| `nDCG@5` | 0.7039 | 0.1815 | -0.5224 |
| `nDCG@10` | 0.7039 | 0.1815 | -0.5224 |
| `precision@5` | 0.4000 | 0.2000 | -0.2000 |

### Expected source 的 rank 变化

| Expected source | Baseline rank | Rerank rank | Change |
|---|---:|---:|---:|
| `ch01/s07_chunk_01.md` | 1 | 5 | +4 |
| `ch01/s07_chunk_03.md` | — | — | — |
| `ch01/s07_chunk_04.md` | 3 | — | — |

### Top 5 变动

- 移出 Top 5（baseline → rerank）：`ch01/s07_chunk_04.md`, `ch02/s06_chunk_02.md`
- 移入 Top 5（rerank 相对 baseline）：`ch01/s08_chunk_01.md`, `ch01/s08_chunk_02.md`

#### Baseline Top 10

| Rank | Source | Title | Score | Rerank score |
|---:|---|---|---:|---:|
| 1 | `ch01/s07_chunk_01.md` | 第六节　创造顾客的六条路径 | 0.9971 | — |
| 2 | `ch05/s02_chunk_02.md` | 第一节 两个故事：指标的两面 | 0.9623 | — |
| 3 | `ch01/s07_chunk_04.md` | 第六节　创造顾客的六条路径 | 0.9552 | — |
| 4 | `ch02/s06_chunk_02.md` | 第五节 营销的复归：五个相互咬合的环节 | 0.9403 | — |
| 5 | `ch02/s07_chunk_02.md` | 第六节 回归之路：五个核心步骤 | 0.9278 | — |
| 6 | `ch02/s06_chunk_01.md` | 第五节 营销的复归：五个相互咬合的环节 | 0.9138 | — |
| 7 | `ch02/s07_chunk_05.md` | 第六节 回归之路：五个核心步骤 | 0.9092 | — |
| 8 | `ch02/s06_chunk_04.md` | 第五节 营销的复归：五个相互咬合的环节 | 0.8997 | — |
| 9 | `ch04/s05_chunk_01.md` | 第四节 回归本源：让组织服务于战略的方法论 | 0.8970 | — |
| 10 | `ch01/s01.md` | 引言 | 0.8966 | — |

#### Rerank Top 10

| Rank | Source | Title | Score | Rerank score |
|---:|---|---|---:|---:|
| 1 | `ch05/s02_chunk_02.md` | 第一节 两个故事：指标的两面 | 0.9623 | 0.9848 |
| 2 | `ch01/s08_chunk_02.md` | 第七节　把理念变成行动的五个步骤 | 0.8884 | 0.9619 |
| 3 | `ch01/s08_chunk_01.md` | 第七节　把理念变成行动的五个步骤 | 0.8757 | 0.9568 |
| 4 | `ch02/s07_chunk_02.md` | 第六节 回归之路：五个核心步骤 | 0.9278 | 0.8870 |
| 5 | `ch01/s07_chunk_01.md` | 第六节　创造顾客的六条路径 | 0.9971 | 0.8540 |
| 6 | `ch02/s07_chunk_01.md` | 第六节 回归之路：五个核心步骤 | 0.8872 | 0.8446 |
| 7 | `ch01/s01.md` | 引言 | 0.8966 | 0.8442 |
| 8 | `ch01/s05_chunk_04.md` | 第四节　两种逻辑，两种命运 | 0.8856 | 0.8308 |
| 9 | `ch02/s07_chunk_05.md` | 第六节 回归之路：五个核心步骤 | 0.9092 | 0.8061 |
| 10 | `ch02/s07_chunk_03.md` | 第六节 回归之路：五个核心步骤 | 0.8949 | 0.7983 |

## sales_marketing_005

### 基本信息和 query

| Field | Value |
|---|---|
| Topic | `sales_vs_marketing` |
| Query type | `multi_issue` |
| Difficulty | `hard` |
| Query | 营收目标压得很紧，品牌承诺与产品体验不一致，研发和销售各自解释客户流失；如何让市场、价值定义和跨职能行动重新对齐？ |

### Expected sources

`ch02/s04_chunk_03.md`, `ch02/s06_chunk_03.md`, `ch02/s06_chunk_04.md`

### 主要 metrics（final Top 10）

| Metric | Baseline | Rerank | Δ (rerank - baseline) |
|---|---:|---:|---:|
| `hit@1` | 0.0000 | 0.0000 | 0.0000 |
| `hit@3` | 1.0000 | 0.0000 | -1.0000 |
| `hit@5` | 1.0000 | 0.0000 | -1.0000 |
| `recall@5` | 0.6667 | 0.0000 | -0.6667 |
| `recall@10` | 0.6667 | 1.0000 | 0.3333 |
| `mrr@5` | 0.5000 | 0.0000 | -0.5000 |
| `nDCG@5` | 0.5307 | 0.0000 | -0.5307 |
| `nDCG@10` | 0.5307 | 0.4716 | -0.0591 |
| `precision@5` | 0.4000 | 0.0000 | -0.4000 |

### Expected source 的 rank 变化

| Expected source | Baseline rank | Rerank rank | Change |
|---|---:|---:|---:|
| `ch02/s04_chunk_03.md` | — | 7 | — |
| `ch02/s06_chunk_03.md` | 2 | 8 | +6 |
| `ch02/s06_chunk_04.md` | 3 | 6 | +3 |

### Top 5 变动

- 移出 Top 5（baseline → rerank）：`ch02/s06_chunk_03.md`, `ch02/s06_chunk_04.md`
- 移入 Top 5（rerank 相对 baseline）：`ch02/s07_chunk_01.md`, `ch02/s07_chunk_03.md`

#### Baseline Top 10

| Rank | Source | Title | Score | Rerank score |
|---:|---|---|---:|---:|
| 1 | `ch02/s06_chunk_05.md` | 第五节 营销的复归：五个相互咬合的环节 | 0.9963 | — |
| 2 | `ch02/s06_chunk_03.md` | 第五节 营销的复归：五个相互咬合的环节 | 0.9650 | — |
| 3 | `ch02/s06_chunk_04.md` | 第五节 营销的复归：五个相互咬合的环节 | 0.9601 | — |
| 4 | `ch02/s06_chunk_06.md` | 第五节 营销的复归：五个相互咬合的环节 | 0.9460 | — |
| 5 | `ch02/s07_chunk_02.md` | 第六节 回归之路：五个核心步骤 | 0.9111 | — |
| 6 | `ch02/s07_chunk_03.md` | 第六节 回归之路：五个核心步骤 | 0.8911 | — |
| 7 | `ch02/s06_chunk_02.md` | 第五节 营销的复归：五个相互咬合的环节 | 0.8708 | — |
| 8 | `ch02/s02.md` | 第一节 销售何以占据了舞台中央 | 0.8670 | — |
| 9 | `ch05/s01.md` | 引言：指标陷阱 | 0.8635 | — |
| 10 | `ch02/s01.md` | 引言 | 0.8481 | — |

#### Rerank Top 10

| Rank | Source | Title | Score | Rerank score |
|---:|---|---|---:|---:|
| 1 | `ch02/s06_chunk_05.md` | 第五节 营销的复归：五个相互咬合的环节 | 0.9963 | 0.8931 |
| 2 | `ch02/s07_chunk_01.md` | 第六节 回归之路：五个核心步骤 | 0.8466 | 0.8678 |
| 3 | `ch02/s07_chunk_03.md` | 第六节 回归之路：五个核心步骤 | 0.8911 | 0.8525 |
| 4 | `ch02/s07_chunk_02.md` | 第六节 回归之路：五个核心步骤 | 0.9111 | 0.8169 |
| 5 | `ch02/s06_chunk_06.md` | 第五节 营销的复归：五个相互咬合的环节 | 0.9460 | 0.5365 |
| 6 | `ch02/s06_chunk_04.md` | 第五节 营销的复归：五个相互咬合的环节 | 0.9601 | 0.5232 |
| 7 | `ch02/s04_chunk_03.md` | 第三节 正反镜鉴：两种范式，两种命运 | 0.8220 | 0.4936 |
| 8 | `ch02/s06_chunk_03.md` | 第五节 营销的复归：五个相互咬合的环节 | 0.9650 | 0.3889 |
| 9 | `ch02/s06_chunk_02.md` | 第五节 营销的复归：五个相互咬合的环节 | 0.8708 | 0.2986 |
| 10 | `ch05/s05_chunk_02.md` | 第四节 为什么指标总是容易“篡位” | 0.8216 | 0.2873 |

## opportunity_005

### 基本信息和 query

| Field | Value |
|---|---|
| Topic | `opportunity` |
| Query type | `multi_issue` |
| Difficulty | `hard` |
| Query | 新技术、海外市场和大客户项目同时出现，团队既缺人又缺验证时间；如何筛选机会、识别能力边界，并决定先做哪一个？ |

### Expected sources

`ch03/s05_chunk_01.md`, `ch03/s05_chunk_02.md`, `ch03/s06_chunk_02.md`

### 主要 metrics（final Top 10）

| Metric | Baseline | Rerank | Δ (rerank - baseline) |
|---|---:|---:|---:|
| `hit@1` | 0.0000 | 0.0000 | 0.0000 |
| `hit@3` | 1.0000 | 0.0000 | -1.0000 |
| `hit@5` | 1.0000 | 0.0000 | -1.0000 |
| `recall@5` | 0.6667 | 0.0000 | -0.6667 |
| `recall@10` | 0.6667 | 0.3333 | -0.3333 |
| `mrr@5` | 0.3333 | 0.0000 | -0.3333 |
| `nDCG@5` | 0.4162 | 0.0000 | -0.4162 |
| `nDCG@10` | 0.4162 | 0.1672 | -0.2490 |
| `precision@5` | 0.4000 | 0.0000 | -0.4000 |

### Expected source 的 rank 变化

| Expected source | Baseline rank | Rerank rank | Change |
|---|---:|---:|---:|
| `ch03/s05_chunk_01.md` | 3 | 6 | +3 |
| `ch03/s05_chunk_02.md` | 5 | — | — |
| `ch03/s06_chunk_02.md` | — | — | — |

### Top 5 变动

- 移出 Top 5（baseline → rerank）：`ch03/s04.md`, `ch03/s05_chunk_01.md`, `ch03/s05_chunk_02.md`, `ch03/s08_chunk_02.md`
- 移入 Top 5（rerank 相对 baseline）：`ch02/s07_chunk_02.md`, `ch03/s01.md`, `ch03/s08_chunk_04.md`, `ch07/s02_chunk_03.md`

#### Baseline Top 10

| Rank | Source | Title | Score | Rerank score |
|---:|---|---|---:|---:|
| 1 | `ch03/s08_chunk_02.md` | 第七节 让“重视机会”成为系统 | 0.9691 | — |
| 2 | `ch03/s04.md` | 第三节 管理者的新角色：注意力的守门人 | 0.9402 | — |
| 3 | `ch03/s05_chunk_01.md` | 第四节 “重视机会”不是“机会主义” | 0.9293 | — |
| 4 | `ch08/s01_chunk_05.md` | 第一部分 系统思考——看清牵一发而动全身的脉络 | 0.9286 | — |
| 5 | `ch03/s05_chunk_02.md` | 第四节 “重视机会”不是“机会主义” | 0.9256 | — |
| 6 | `ch03/s08_chunk_03.md` | 第七节 让“重视机会”成为系统 | 0.9226 | — |
| 7 | `ch03/s01.md` | 引言：从“问题海洋”到“机会大陆” | 0.9188 | — |
| 8 | `ch07/s06_chunk_02.md` | 第五节 让“为明天决策”成为组织的能力 | 0.9182 | — |
| 9 | `ch05/s07_chunk_02.md` | 第六节 德鲁克的智慧：八大领域的平衡之道 | 0.9177 | — |
| 10 | `ch07/s02_chunk_03.md` | 第一节 为什么“预测与顺应”不是决策的本质 | 0.9158 | — |

#### Rerank Top 10

| Rank | Source | Title | Score | Rerank score |
|---:|---|---|---:|---:|
| 1 | `ch08/s01_chunk_05.md` | 第一部分 系统思考——看清牵一发而动全身的脉络 | 0.9286 | 0.6267 |
| 2 | `ch07/s02_chunk_03.md` | 第一节 为什么“预测与顺应”不是决策的本质 | 0.9158 | 0.3917 |
| 3 | `ch02/s07_chunk_02.md` | 第六节 回归之路：五个核心步骤 | 0.8883 | 0.2428 |
| 4 | `ch03/s01.md` | 引言：从“问题海洋”到“机会大陆” | 0.9188 | 0.2179 |
| 5 | `ch03/s08_chunk_04.md` | 第七节 让“重视机会”成为系统 | 0.9033 | 0.1084 |
| 6 | `ch03/s05_chunk_01.md` | 第四节 “重视机会”不是“机会主义” | 0.9293 | 0.1039 |
| 7 | `ch03/s08_chunk_03.md` | 第七节 让“重视机会”成为系统 | 0.9226 | 0.1008 |
| 8 | `ch03/s08_chunk_02.md` | 第七节 让“重视机会”成为系统 | 0.9691 | 0.0951 |
| 9 | `ch03/s04.md` | 第三节 管理者的新角色：注意力的守门人 | 0.9402 | 0.0935 |
| 10 | `ch03/s05_chunk_03.md` | 第四节 “重视机会”不是“机会主义” | 0.9035 | 0.0714 |

## strategy_org_003

### 基本信息和 query

| Field | Value |
|---|---|
| Topic | `strategy_organization` |
| Query type | `direct_concept` |
| Difficulty | `easy` |
| Query | 组织结构为什么必须服务于战略，战略变化时应观察哪些结构性后果？ |

### Expected sources

`ch04/s02.md`, `ch04/s04_chunk_01.md`, `ch04/s05_chunk_01.md`

### 主要 metrics（final Top 10）

| Metric | Baseline | Rerank | Δ (rerank - baseline) |
|---|---:|---:|---:|
| `hit@1` | 1.0000 | 0.0000 | -1.0000 |
| `hit@3` | 1.0000 | 0.0000 | -1.0000 |
| `hit@5` | 1.0000 | 0.0000 | -1.0000 |
| `recall@5` | 0.6667 | 0.0000 | -0.6667 |
| `recall@10` | 1.0000 | 1.0000 | 0.0000 |
| `mrr@5` | 1.0000 | 0.0000 | -1.0000 |
| `nDCG@5` | 0.6508 | 0.0000 | -0.6508 |
| `nDCG@10` | 0.7989 | 0.4250 | -0.3739 |
| `precision@5` | 0.4000 | 0.0000 | -0.4000 |

### Expected source 的 rank 变化

| Expected source | Baseline rank | Rerank rank | Change |
|---|---:|---:|---:|
| `ch04/s02.md` | 8 | 10 | +2 |
| `ch04/s04_chunk_01.md` | 5 | 8 | +3 |
| `ch04/s05_chunk_01.md` | 1 | 9 | +8 |

### Top 5 变动

- 移出 Top 5（baseline → rerank）：`ch04/s04_chunk_01.md`, `ch04/s05_chunk_01.md`
- 移入 Top 5（rerank 相对 baseline）：`ch04/s03_chunk_03.md`, `ch04/s03_chunk_04.md`

#### Baseline Top 10

| Rank | Source | Title | Score | Rerank score |
|---:|---|---|---:|---:|
| 1 | `ch04/s05_chunk_01.md` | 第四节 回归本源：让组织服务于战略的方法论 | 0.9442 | — |
| 2 | `ch04/s04_chunk_02.md` | 第三节 现实的冲突：为何“战略决定结构”知易行难 | 0.9248 | — |
| 3 | `ch04/s05_chunk_05.md` | 第四节 回归本源：让组织服务于战略的方法论 | 0.9158 | — |
| 4 | `ch04/s06_chunk_03.md` | 第五节 组织偏离战略的五个信号 信号即行动号角。 | 0.9109 | — |
| 5 | `ch04/s04_chunk_01.md` | 第三节 现实的冲突：为何“战略决定结构”知易行难 | 0.9053 | — |
| 6 | `ch04/s01.md` | 引言 | 0.8963 | — |
| 7 | `ch04/s03_chunk_04.md` | 第二节 正反镜鉴：组织如何成为战略的加速器或刹车片 | 0.8833 | — |
| 8 | `ch04/s02.md` | 第一节 迷失：当组织设计偏离战略原点 | 0.8814 | — |
| 9 | `ch04/s05_chunk_06.md` | 第四节 回归本源：让组织服务于战略的方法论 | 0.8794 | — |
| 10 | `ch04/s06_chunk_02.md` | 第五节 组织偏离战略的五个信号 信号即行动号角。 | 0.8718 | — |

#### Rerank Top 10

| Rank | Source | Title | Score | Rerank score |
|---:|---|---|---:|---:|
| 1 | `ch04/s06_chunk_03.md` | 第五节 组织偏离战略的五个信号 信号即行动号角。 | 0.9109 | 0.9861 |
| 2 | `ch04/s03_chunk_04.md` | 第二节 正反镜鉴：组织如何成为战略的加速器或刹车片 | 0.8833 | 0.9730 |
| 3 | `ch04/s05_chunk_05.md` | 第四节 回归本源：让组织服务于战略的方法论 | 0.9158 | 0.9461 |
| 4 | `ch04/s04_chunk_02.md` | 第三节 现实的冲突：为何“战略决定结构”知易行难 | 0.9248 | 0.9317 |
| 5 | `ch04/s03_chunk_03.md` | 第二节 正反镜鉴：组织如何成为战略的加速器或刹车片 | 0.8567 | 0.9131 |
| 6 | `ch04/s06_chunk_02.md` | 第五节 组织偏离战略的五个信号 信号即行动号角。 | 0.8718 | 0.8598 |
| 7 | `ch04/s01.md` | 引言 | 0.8963 | 0.8419 |
| 8 | `ch04/s04_chunk_01.md` | 第三节 现实的冲突：为何“战略决定结构”知易行难 | 0.9053 | 0.7038 |
| 9 | `ch04/s05_chunk_01.md` | 第四节 回归本源：让组织服务于战略的方法论 | 0.9442 | 0.6991 |
| 10 | `ch04/s02.md` | 第一节 迷失：当组织设计偏离战略原点 | 0.8814 | 0.6886 |

## metrics_004

### 基本信息和 query

| Field | Value |
|---|---|
| Topic | `metrics` |
| Query type | `semantic_rewrite` |
| Difficulty | `medium` |
| Query | 客服为了降低平均处理时长而草草结案，数字变漂亮了但投诉和流失上升；应该怎样重看这个指标？ |

### Expected sources

`ch05/s04_chunk_01.md`, `ch05/s04_chunk_03.md`, `ch05/s05_chunk_02.md`

### 主要 metrics（final Top 10）

| Metric | Baseline | Rerank | Δ (rerank - baseline) |
|---|---:|---:|---:|
| `hit@1` | 0.0000 | 0.0000 | 0.0000 |
| `hit@3` | 0.0000 | 0.0000 | 0.0000 |
| `hit@5` | 1.0000 | 0.0000 | -1.0000 |
| `recall@5` | 0.6667 | 0.0000 | -0.6667 |
| `recall@10` | 0.6667 | 0.0000 | -0.6667 |
| `mrr@5` | 0.2500 | 0.0000 | -0.2500 |
| `nDCG@5` | 0.3836 | 0.0000 | -0.3836 |
| `nDCG@10` | 0.3836 | 0.0000 | -0.3836 |
| `precision@5` | 0.4000 | 0.0000 | -0.4000 |

### Expected source 的 rank 变化

| Expected source | Baseline rank | Rerank rank | Change |
|---|---:|---:|---:|
| `ch05/s04_chunk_01.md` | — | — | — |
| `ch05/s04_chunk_03.md` | 4 | — | — |
| `ch05/s05_chunk_02.md` | 5 | — | — |

### Top 5 变动

- 移出 Top 5（baseline → rerank）：`ch05/s04_chunk_03.md`, `ch05/s05_chunk_02.md`, `ch05/s08_chunk_02.md`
- 移入 Top 5（rerank 相对 baseline）：`ch02/s06_chunk_06.md`, `ch08/s01_chunk_02.md`, `ch08/s01_chunk_03.md`

#### Baseline Top 10

| Rank | Source | Title | Score | Rerank score |
|---:|---|---|---:|---:|
| 1 | `ch05/s02_chunk_03.md` | 第一节 两个故事：指标的两面 | 0.9097 | — |
| 2 | `ch05/s04_chunk_02.md` | 第三节 指标偏离的三重代价 | 0.8888 | — |
| 3 | `ch05/s08_chunk_02.md` | 本章小结 | 0.8837 | — |
| 4 | `ch05/s04_chunk_03.md` | 第三节 指标偏离的三重代价 | 0.8648 | — |
| 5 | `ch05/s05_chunk_02.md` | 第四节 为什么指标总是容易“篡位” | 0.8591 | — |
| 6 | `ch02/s06_chunk_06.md` | 第五节 营销的复归：五个相互咬合的环节 | 0.8567 | — |
| 7 | `ch08/s01_chunk_02.md` | 第一部分 系统思考——看清牵一发而动全身的脉络 | 0.8558 | — |
| 8 | `ch05/s06_chunk_02.md` | 第五节 让衡量回归正途：五个阶段 | 0.8553 | — |
| 9 | `ch08/s01_chunk_03.md` | 第一部分 系统思考——看清牵一发而动全身的脉络 | 0.8415 | — |
| 10 | `ch05/s01.md` | 引言：指标陷阱 | 0.8319 | — |

#### Rerank Top 10

| Rank | Source | Title | Score | Rerank score |
|---:|---|---|---:|---:|
| 1 | `ch08/s01_chunk_03.md` | 第一部分 系统思考——看清牵一发而动全身的脉络 | 0.8415 | 0.4727 |
| 2 | `ch02/s06_chunk_06.md` | 第五节 营销的复归：五个相互咬合的环节 | 0.8567 | 0.3029 |
| 3 | `ch08/s01_chunk_02.md` | 第一部分 系统思考——看清牵一发而动全身的脉络 | 0.8558 | 0.2805 |
| 4 | `ch05/s02_chunk_03.md` | 第一节 两个故事：指标的两面 | 0.9097 | 0.2606 |
| 5 | `ch05/s04_chunk_02.md` | 第三节 指标偏离的三重代价 | 0.8888 | 0.1970 |
| 6 | `ch05/s02_chunk_02.md` | 第一节 两个故事：指标的两面 | 0.8036 | 0.1752 |
| 7 | `ch05/s06_chunk_02.md` | 第五节 让衡量回归正途：五个阶段 | 0.8553 | 0.1716 |
| 8 | `ch05/s08_chunk_01.md` | 本章小结 | 0.7907 | 0.1005 |
| 9 | `ch05/s01.md` | 引言：指标陷阱 | 0.8319 | 0.1000 |
| 10 | `ch01/s08_chunk_02.md` | 第七节　把理念变成行动的五个步骤 | 0.7926 | 0.0744 |

## self_drive_001

### 基本信息和 query

| Field | Value |
|---|---|
| Topic | `self_drive` |
| Query type | `semantic_rewrite` |
| Difficulty | `medium` |
| Query | 员工只等指令，管理层不断增加审批和过程监控，目标管理变成了目标控制。 |

### Expected sources

`ch06/s01.md`, `ch06/s03_chunk_01.md`, `ch06/s03_chunk_02.md`

### 主要 metrics（final Top 10）

| Metric | Baseline | Rerank | Δ (rerank - baseline) |
|---|---:|---:|---:|
| `hit@1` | 1.0000 | 1.0000 | 0.0000 |
| `hit@3` | 1.0000 | 1.0000 | 0.0000 |
| `hit@5` | 1.0000 | 1.0000 | 0.0000 |
| `recall@5` | 1.0000 | 0.6667 | -0.3333 |
| `recall@10` | 1.0000 | 1.0000 | 0.0000 |
| `mrr@5` | 1.0000 | 1.0000 | 0.0000 |
| `nDCG@5` | 0.8855 | 0.6714 | -0.2141 |
| `nDCG@10` | 0.8855 | 0.8385 | -0.0469 |
| `precision@5` | 0.6000 | 0.4000 | -0.2000 |

### Expected source 的 rank 变化

| Expected source | Baseline rank | Rerank rank | Change |
|---|---:|---:|---:|
| `ch06/s01.md` | 3 | 4 | +1 |
| `ch06/s03_chunk_01.md` | 5 | 6 | +1 |
| `ch06/s03_chunk_02.md` | 1 | 1 | 0 |

### Top 5 变动

- 移出 Top 5（baseline → rerank）：`ch06/s03_chunk_01.md`, `ch06/s06_chunk_01.md`
- 移入 Top 5（rerank 相对 baseline）：`ch06/s07.md`, `ch07/s01_chunk_01.md`

#### Baseline Top 10

| Rank | Source | Title | Score | Rerank score |
|---:|---|---|---:|---:|
| 1 | `ch06/s03_chunk_02.md` | 第二节 从目标管理到目标控制——偏离是如何发生的 | 1.0000 | — |
| 2 | `ch06/s03_chunk_03.md` | 第二节 从目标管理到目标控制——偏离是如何发生的 | 0.8827 | — |
| 3 | `ch06/s01.md` | 引言：一个普遍的困惑 | 0.8687 | — |
| 4 | `ch06/s06_chunk_01.md` | 第五节 回归之路——如何实现真正的自我控制 | 0.8577 | — |
| 5 | `ch06/s03_chunk_01.md` | 第二节 从目标管理到目标控制——偏离是如何发生的 | 0.8567 | — |
| 6 | `ch06/s06_chunk_02.md` | 第五节 回归之路——如何实现真正的自我控制 | 0.8498 | — |
| 7 | `ch06/s05_chunk_02.md` | 第四节 现实张力——为什么企业难以自拔 | 0.8401 | — |
| 8 | `ch06/s04_chunk_01.md` | 第三节 两条道路：控制与信任的对照 | 0.8223 | — |
| 9 | `ch06/s07.md` | 本章小结 | 0.8202 | — |
| 10 | `ch06/s04_chunk_02.md` | 第三节 两条道路：控制与信任的对照 | 0.8185 | — |

#### Rerank Top 10

| Rank | Source | Title | Score | Rerank score |
|---:|---|---|---:|---:|
| 1 | `ch06/s03_chunk_02.md` | 第二节 从目标管理到目标控制——偏离是如何发生的 | 1.0000 | 0.9940 |
| 2 | `ch06/s03_chunk_03.md` | 第二节 从目标管理到目标控制——偏离是如何发生的 | 0.8827 | 0.9878 |
| 3 | `ch07/s01_chunk_01.md` | 引言 | 0.8181 | 0.9495 |
| 4 | `ch06/s01.md` | 引言：一个普遍的困惑 | 0.8687 | 0.9462 |
| 5 | `ch06/s07.md` | 本章小结 | 0.8202 | 0.9412 |
| 6 | `ch06/s03_chunk_01.md` | 第二节 从目标管理到目标控制——偏离是如何发生的 | 0.8567 | 0.8973 |
| 7 | `ch06/s04_chunk_02.md` | 第三节 两条道路：控制与信任的对照 | 0.8185 | 0.8871 |
| 8 | `ch06/s05_chunk_02.md` | 第四节 现实张力——为什么企业难以自拔 | 0.8401 | 0.8754 |
| 9 | `ch06/s04_chunk_04.md` | 第三节 两条道路：控制与信任的对照 | 0.8140 | 0.8690 |
| 10 | `ch06/s06_chunk_02.md` | 第五节 回归之路——如何实现真正的自我控制 | 0.8498 | 0.8523 |

## long_term_decision_005

### 基本信息和 query

| Field | Value |
|---|---|
| Topic | `long_term_decision` |
| Query type | `multi_issue` |
| Difficulty | `hard` |
| Query | 现金流只够支持一个方向，公司要在核心业务优化、下一代产品试验和组织能力建设之间取舍；如何分层投入并兼顾今天与未来？ |

### Expected sources

`ch07/s03_chunk_01.md`, `ch07/s03_chunk_03.md`, `ch07/s07_chunk_02.md`

### 主要 metrics（final Top 10）

| Metric | Baseline | Rerank | Δ (rerank - baseline) |
|---|---:|---:|---:|
| `hit@1` | 1.0000 | 0.0000 | -1.0000 |
| `hit@3` | 1.0000 | 0.0000 | -1.0000 |
| `hit@5` | 1.0000 | 0.0000 | -1.0000 |
| `recall@5` | 0.3333 | 0.0000 | -0.3333 |
| `recall@10` | 0.3333 | 0.3333 | 0.0000 |
| `mrr@5` | 1.0000 | 0.0000 | -1.0000 |
| `nDCG@5` | 0.4693 | 0.0000 | -0.4693 |
| `nDCG@10` | 0.4693 | 0.1564 | -0.3129 |
| `precision@5` | 0.2000 | 0.0000 | -0.2000 |

### Expected source 的 rank 变化

| Expected source | Baseline rank | Rerank rank | Change |
|---|---:|---:|---:|
| `ch07/s03_chunk_01.md` | — | — | — |
| `ch07/s03_chunk_03.md` | 1 | 7 | +6 |
| `ch07/s07_chunk_02.md` | — | — | — |

### Top 5 变动

- 移出 Top 5（baseline → rerank）：`ch01/s03_chunk_02.md`, `ch07/s03_chunk_03.md`, `ch07/s07_chunk_01.md`
- 移入 Top 5（rerank 相对 baseline）：`ch01/s04_chunk_01.md`, `ch07/s03_chunk_02.md`, `ch07/s05_chunk_03.md`

#### Baseline Top 10

| Rank | Source | Title | Score | Rerank score |
|---:|---|---|---:|---:|
| 1 | `ch07/s03_chunk_03.md` | 第二节 长期建构与短期生存的永恒博弈 | 0.9344 | — |
| 2 | `ch07/s07_chunk_01.md` | 本章小结 | 0.9320 | — |
| 3 | `ch01/s03_chunk_02.md` | 第二节　直面矛盾：理想与现实之间的博弈 | 0.9119 | — |
| 4 | `ch08/s01_chunk_04.md` | 第一部分 系统思考——看清牵一发而动全身的脉络 | 0.9075 | — |
| 5 | `ch03/s08_chunk_02.md` | 第七节 让“重视机会”成为系统 | 0.9037 | — |
| 6 | `ch07/s06_chunk_02.md` | 第五节 让“为明天决策”成为组织的能力 | 0.8935 | — |
| 7 | `ch07/s04_chunk_01.md` | 第三节 两条道路：拥抱未来与守护过去的命运分野 | 0.8841 | — |
| 8 | `ch07/s04_chunk_04.md` | 第三节 两条道路：拥抱未来与守护过去的命运分野 | 0.8740 | — |
| 9 | `ch01/s04_chunk_02.md` | 第三节　平衡价值与利润的五种方法 | 0.8691 | — |
| 10 | `ch08/s02_chunk_03.md` | 第二部分 决策勇气——在价值观的基石上拒绝摇摆 | 0.8671 | — |

#### Rerank Top 10

| Rank | Source | Title | Score | Rerank score |
|---:|---|---|---:|---:|
| 1 | `ch07/s05_chunk_03.md` | 第四节 好决策从哪里来 | 0.8351 | 0.8363 |
| 2 | `ch07/s03_chunk_02.md` | 第二节 长期建构与短期生存的永恒博弈 | 0.8460 | 0.6010 |
| 3 | `ch03/s08_chunk_02.md` | 第七节 让“重视机会”成为系统 | 0.9037 | 0.5365 |
| 4 | `ch01/s04_chunk_01.md` | 第三节　平衡价值与利润的五种方法 | 0.8402 | 0.4930 |
| 5 | `ch08/s01_chunk_04.md` | 第一部分 系统思考——看清牵一发而动全身的脉络 | 0.9075 | 0.3689 |
| 6 | `ch01/s03_chunk_02.md` | 第二节　直面矛盾：理想与现实之间的博弈 | 0.9119 | 0.2561 |
| 7 | `ch07/s03_chunk_03.md` | 第二节 长期建构与短期生存的永恒博弈 | 0.9344 | 0.2177 |
| 8 | `ch07/s07_chunk_01.md` | 本章小结 | 0.9320 | 0.1910 |
| 9 | `ch01/s04_chunk_02.md` | 第三节　平衡价值与利润的五种方法 | 0.8691 | 0.1493 |
| 10 | `ch07/s06_chunk_02.md` | 第五节 让“为明天决策”成为组织的能力 | 0.8935 | 0.1493 |

## entrepreneurship_001

### 基本信息和 query

| Field | Value |
|---|---|
| Topic | `entrepreneurship` |
| Query type | `semantic_rewrite` |
| Difficulty | `medium` |
| Query | 企业家面对复杂问题时，不能只修补局部，要如何用系统思考看清因果和整体最优？ |

### Expected sources

`ch08/s01_chunk_01.md`, `ch08/s01_chunk_04.md`, `ch08/s01_chunk_07.md`

### 主要 metrics（final Top 10）

| Metric | Baseline | Rerank | Δ (rerank - baseline) |
|---|---:|---:|---:|
| `hit@1` | 0.0000 | 0.0000 | 0.0000 |
| `hit@3` | 1.0000 | 0.0000 | -1.0000 |
| `hit@5` | 1.0000 | 1.0000 | 0.0000 |
| `recall@5` | 0.6667 | 0.3333 | -0.3333 |
| `recall@10` | 1.0000 | 1.0000 | 0.0000 |
| `mrr@5` | 0.5000 | 0.2500 | -0.2500 |
| `nDCG@5` | 0.5307 | 0.2021 | -0.3286 |
| `nDCG@10` | 0.6979 | 0.5257 | -0.1722 |
| `precision@5` | 0.4000 | 0.2000 | -0.2000 |

### Expected source 的 rank 变化

| Expected source | Baseline rank | Rerank rank | Change |
|---|---:|---:|---:|
| `ch08/s01_chunk_01.md` | 6 | 7 | +1 |
| `ch08/s01_chunk_04.md` | 3 | 4 | +1 |
| `ch08/s01_chunk_07.md` | 2 | 6 | +4 |

### Top 5 变动

- 移出 Top 5（baseline → rerank）：`ch08/s01_chunk_07.md`
- 移入 Top 5（rerank 相对 baseline）：`ch08/s01_chunk_08.md`

#### Baseline Top 10

| Rank | Source | Title | Score | Rerank score |
|---:|---|---|---:|---:|
| 1 | `ch08/s01_chunk_06.md` | 第一部分 系统思考——看清牵一发而动全身的脉络 | 0.9528 | — |
| 2 | `ch08/s01_chunk_07.md` | 第一部分 系统思考——看清牵一发而动全身的脉络 | 0.9402 | — |
| 3 | `ch08/s01_chunk_04.md` | 第一部分 系统思考——看清牵一发而动全身的脉络 | 0.9340 | — |
| 4 | `ch08/s01_chunk_02.md` | 第一部分 系统思考——看清牵一发而动全身的脉络 | 0.9225 | — |
| 5 | `ch08/s01_chunk_03.md` | 第一部分 系统思考——看清牵一发而动全身的脉络 | 0.8909 | — |
| 6 | `ch08/s01_chunk_01.md` | 第一部分 系统思考——看清牵一发而动全身的脉络 | 0.8817 | — |
| 7 | `ch08/s01_chunk_05.md` | 第一部分 系统思考——看清牵一发而动全身的脉络 | 0.8777 | — |
| 8 | `ch03/s03.md` | 第二节 为什么“问题”总是赢家 | 0.8269 | — |
| 9 | `ch01/s03_chunk_03.md` | 第二节　直面矛盾：理想与现实之间的博弈 | 0.8104 | — |
| 10 | `ch03/s01.md` | 引言：从“问题海洋”到“机会大陆” | 0.8016 | — |

#### Rerank Top 10

| Rank | Source | Title | Score | Rerank score |
|---:|---|---|---:|---:|
| 1 | `ch08/s01_chunk_06.md` | 第一部分 系统思考——看清牵一发而动全身的脉络 | 0.9528 | 0.9963 |
| 2 | `ch08/s01_chunk_03.md` | 第一部分 系统思考——看清牵一发而动全身的脉络 | 0.8909 | 0.9912 |
| 3 | `ch08/s01_chunk_08.md` | 第一部分 系统思考——看清牵一发而动全身的脉络 | 0.7993 | 0.9842 |
| 4 | `ch08/s01_chunk_04.md` | 第一部分 系统思考——看清牵一发而动全身的脉络 | 0.9340 | 0.9830 |
| 5 | `ch08/s01_chunk_02.md` | 第一部分 系统思考——看清牵一发而动全身的脉络 | 0.9225 | 0.9758 |
| 6 | `ch08/s01_chunk_07.md` | 第一部分 系统思考——看清牵一发而动全身的脉络 | 0.9402 | 0.9648 |
| 7 | `ch08/s01_chunk_01.md` | 第一部分 系统思考——看清牵一发而动全身的脉络 | 0.8817 | 0.9581 |
| 8 | `ch08/s01_chunk_05.md` | 第一部分 系统思考——看清牵一发而动全身的脉络 | 0.8777 | 0.9108 |
| 9 | `ch08/s00_chunk_02.md` | 第八章 管理的终极回归——企业家的三重修炼 | 0.7674 | 0.8969 |
| 10 | `ch08/s04.md` | 本章小结 | 0.7821 | 0.7371 |


# Management Diagnosis Agent

A local workflow-based AI Agent prototype for management diagnosis. The project combines FastAPI, LangGraph, Ollama, a private management knowledge base, and a hybrid RAG retrieval pipeline.

The current goal is learning and demonstrating practical Agent/RAG engineering skills: workflow orchestration, controlled tool use, local retrieval, embedding-based search, hybrid retrieval, and retrieval evaluation.

---

## Current Implementation

- FastAPI backend service
- LangGraph workflow orchestration
- Local LLM generation through Ollama
- Qwen3 8B local model by default
- Private-only management knowledge retrieval
- Structured markdown chunking with chunk statistics
- Hugging Face embedding model cached locally
- Local vector index using JSON + NumPy `.npy`
- Hybrid retrieval combining keyword and embedding search
- Retrieval debug script for manual inspection
- Retrieval eval dataset and experiment tracking
- Rule-based report verification
- One-step revision loop when verification fails
- Local project memory persistence

---

## Agent Workflow

The project is a controlled workflow Agent, not a fully autonomous tool-calling Agent. The LLM does not freely choose every next step; LangGraph controls the workflow.

```text
+-------------+
| User Input |
+-------------+
       |
       v
+-------------+
| Intake      |
+-------------+
       |
       v
+-------------+
| Route       |
+-------------+
       |
       v
+-------------+
| Retrieve    |  hybrid RAG
+-------------+
       |
       v
+-------------+
| Generate    |  Ollama / Qwen
+-------------+
       |
       v
+-------------+
| Verify      |
+-------------+
    |      |
    | pass | fail and revision_count < 1
    v      v
+-------------+      +-------------+
| Memory      | <--- | Revise      |
+-------------+      +-------------+
       |
       v
+-------------+
| Response    |
+-------------+
```

Main node implementation:

```text
app/agent/graph.py
app/agent/nodes.py
app/agent/prompts.py
```

---

## Retrieval Architecture

The original retrieval was keyword-only. The current version uses hybrid retrieval:

```text
retrieve_relevant_chunks()
  -> keyword retriever
  -> embedding retriever
  -> score fusion
  -> top_k chunks
```

Current public retrieval entrypoint:

```text
app/rag/retriever.py
```

Retrieval modules:

```text
app/rag/retrieval/
  keyword_retriever.py
  embedding_retriever.py
  hybrid_retriever.py
```

Current default hybrid parameters:

```text
keyword_weight = 0.15
embedding_weight = 0.85
candidate_multiplier = 5
min_candidates = 25
```

These can be overridden with environment variables:

```env
HYBRID_KEYWORD_WEIGHT=0.15
HYBRID_EMBEDDING_WEIGHT=0.85
HYBRID_CANDIDATE_MULTIPLIER=5
HYBRID_MIN_CANDIDATES=25
```

---

## Knowledge Base And Chunking

The private knowledge base is generated from the local source manuscript and ignored by Git:

```text
source_docs/
data/private_knowledge_base/
```

Chunking script:

```powershell
uv run python scripts\split_markdown_kb.py
```

The chunker uses a structured strategy:

```text
markdown headings
-> paragraph packing
-> sentence fallback for long paragraphs
-> small overlap between adjacent chunks
```

Current generated private chunk stats:

```text
chunks: 172
min_chars: 91
max_chars: 1189
avg_chars: 719
```

Generate chunk stats:

```powershell
uv run python scripts\chunk_stats.py --json-out data\chunk_stats.json --csv-out data\chunk_stats.csv
```

---

## Embedding And Vector Index

Embedding model:

```text
BAAI/bge-small-zh-v1.5
```

The model is cached locally:

```text
.hf_cache/
```

Recommended `.env` values:

```env
EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5
HF_HOME=D:\management_diagnosis_agent\.hf_cache
EMBEDDING_LOCAL_FILES_ONLY=true
```

Build the private-only vector index:

```powershell
uv run python scripts\build_vector_index.py
```

Generated vector index files:

```text
data/vector_index/
  knowledge_chunks.json
  knowledge_embeddings.npy
  index_metadata.json
```

`knowledge_chunks.json` stores the retrievable chunk text and metadata. `knowledge_embeddings.npy` stores the corresponding embedding matrix. Row `i` in the `.npy` file corresponds to item `i` in `knowledge_chunks.json`.

Current vector index:

```text
knowledge_scope: private
chunk_count: 172
embedding_dim: 512
```

---

## Retrieval Debugging

To inspect retrieval without calling the LLM:

```powershell
uv run python scripts\debug_retrieval.py "公司增长放缓，客户价值不清晰，团队只盯KPI" --top-k 3
```

The script prints three result sets:

```text
Keyword
Embedding
Hybrid
```

Each result includes:

```text
source
title
retrieval_method
score
keyword_score
embedding_score
hybrid_score
preview
```

---

## Retrieval Evaluation

Eval cases:

```text
tests/evals/retrieval_cases.json
```

The eval script compares:

```text
keyword
embedding
hybrid
```

Metrics:

```text
Hit@3
Hit@5
Recall@5
MRR@5
```

Run retrieval eval:

```powershell
uv run python scripts\eval_retrieval.py
```

Write a JSON report:

```powershell
uv run python scripts\eval_retrieval.py --json-out data\retrieval_eval_report.json
```

Record an experiment:

```powershell
uv run python scripts\eval_retrieval.py `
  --record-experiment `
  --experiment-name linear_015_085_candidates_5x25 `
  --notes "Selected default hybrid retrieval parameters."
```

Experiment history:

```text
tests/evals/retrieval_experiments.jsonl
tests/evals/retrieval_experiments.md
```

Current selected experiment:

```text
linear_015_085_candidates_5x25
```

Current recorded results:

```text
keyword   hit@3 0.375 | hit@5 0.438 | recall@5 0.167 | mrr@5 0.245
embedding hit@3 0.625 | hit@5 0.812 | recall@5 0.458 | mrr@5 0.481
hybrid    hit@3 0.562 | hit@5 0.812 | recall@5 0.438 | mrr@5 0.588
```

Interpretation: embedding has the strongest pure recall coverage, while the selected hybrid setup preserves Hit@5 close to embedding and improves MRR@5, meaning the first relevant result is ranked earlier on this eval set.

---

## API Usage

Start the backend:

```powershell
uv run uvicorn app.main:app --reload
```

Open API docs:

```text
http://127.0.0.1:8000/docs
```

Health check:

```http
GET /health
```

Diagnosis endpoint:

```http
POST /diagnose
```

Request:

```json
{
  "description": "我们公司最近增长放缓，团队每天都很忙，但新客户越来越少。管理层主要在抓成本和效率，员工只是在完成 KPI。请帮我判断主要管理问题，并给出下一步建议。"
}
```

Admin debug endpoint:

```http
POST /admin/diagnose
```

The public endpoint hides full retrieved content. The admin endpoint returns full retrieved source content for debugging.

---

## Project Structure

```text
app/
  agent/
    graph.py
    nodes.py
    prompts.py
    state.py
  llm/
    ollama_client.py
  memory/
    project_memory.py
  rag/
    chunker.py
    embeddings.py
    ingest.py
    retriever.py
    vector_store.py
    retrieval/
      keyword_retriever.py
      embedding_retriever.py
      hybrid_retriever.py
  tools/
    diagnosis_tools.py
    language_tool.py
    problem_router_tool.py
    verify_tool.py
  schemas/
    request.py
    response.py

scripts/
  split_markdown_kb.py
  chunk_stats.py
  build_vector_index.py
  debug_retrieval.py
  eval_retrieval.py

tests/
  evals/
    retrieval_cases.json
    retrieval_experiments.jsonl
    retrieval_experiments.md
```

---

## Tests

Run tests:

```powershell
uv run python -m pytest
```

Run retriever tests only:

```powershell
uv run python -m pytest tests\test_retriever.py
```

Pytest temp files are configured to use:

```text
.pytest_run_tmp/
```

---

## Current Limitations

- Eval cases are small and manually labeled.
- Expected sources may be incomplete and should be refined over time.
- Hybrid fusion is still linear score fusion; RRF or reranking may perform better.
- Memory is saved but not yet retrieved as part of context.
- Verification is rule-based rather than semantic or LLM-as-judge.
- The workflow is controlled and mostly fixed, not a fully autonomous tool-selection Agent.
- There is no frontend yet.

---

## Roadmap

Short-term:

- Improve retrieval eval cases.
- Add RRF fusion and compare against linear fusion.
- Add query rewrite when retrieval quality is weak.
- Add retrieval quality checks before generation.
- Document retrieval experiments in README.

Medium-term:

- Add memory retrieval from previous project records.
- Add reranking.
- Add source-grounding verification.
- Add clarification node for vague inputs.
- Add tracing and node-level logging.

Long-term:

- Add Chroma, Qdrant, or pgvector.
- Add a frontend.
- Add LLM-as-judge evaluation.
- Move from controlled workflow Agent toward more dynamic tool planning.

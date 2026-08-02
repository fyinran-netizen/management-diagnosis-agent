# Management Diagnosis Agent

A local workflow-based AI Agent prototype for management diagnosis.

The current implementation combines LangGraph, Ollama, a private management knowledge base, local embedding retrieval, hybrid RAG, report verification, project memory, and a Streamlit interface for running and inspecting Agent diagnoses.

---

## Current Agent Workflow

This is a controlled workflow Agent. LangGraph owns the execution flow and branch decisions. The LLM generates and revises reports, but it does not freely choose arbitrary tools.

```text
User Input
  -> Intake
  -> Problem Check
      -> if unclear: Clarification Response
  -> Route Problem
  -> Retrieve Knowledge
  -> Retrieval Quality Check
      -> if weak: Low-confidence Response
  -> Diagnose
  -> Generate Report
  -> Verify
      -> if failed and revision_count < 1: Revise
  -> Save Memory
  -> Response
```

Main implementation:

```text
app/agent/graph.py
app/agent/nodes.py
app/agent/prompts.py
app/agent/state.py
```

Supporting tools:

```text
app/tools/problem_check_tool.py
app/tools/problem_router_tool.py
app/tools/retrieval_quality_tool.py
app/tools/diagnosis_tools.py
app/tools/verify_tool.py
app/tools/language_tool.py
```

---

## Current RAG Flow

The current retriever uses local private knowledge only.

```text
private markdown knowledge base
  -> structured chunks
  -> BAAI/bge-small-zh-v1.5 embeddings
  -> local JSON + NumPy vector index
  -> keyword retrieval
  -> embedding retrieval
  -> linear hybrid score fusion
  -> top_k chunks
```

Current default hybrid parameters:

```text
keyword_weight = 0.15
embedding_weight = 0.85
candidate_multiplier = 5
min_candidates = 25
```

Current vector index:

```text
knowledge_scope: private
chunk_count: 172
embedding_dim: 512
```

RAG implementation:

```text
app/rag/embeddings.py
app/rag/vector_store.py
app/rag/retriever.py
app/rag/retrieval/keyword_retriever.py
app/rag/retrieval/embedding_retriever.py
app/rag/retrieval/hybrid_retriever.py
app/rag/retrieval/hybrid_retriever_rrf.py
```

Build the vector index:

```powershell
uv run python scripts\build_vector_index.py
```

Debug retrieval:

```powershell
uv run python scripts\debug_retrieval.py "公司增长放缓，客户价值不清晰，团队只盯 KPI" --top-k 3
```

---

## Streamlit App

Run the Streamlit interface:

```powershell
uv run streamlit run streamlit_app.py
```

The Streamlit app directly calls the local Agent workflow and displays:

```text
input case
diagnosis report
verification result
Agent timeline trace
retrieved source chunks
raw Agent state
```

Ollama must be running before diagnosis generation. The default configuration is:

```text
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3
```

You can override these values in `.env`.

---

## Optional API

The FastAPI service is still available for programmatic access.

Start the API:

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

Public diagnosis endpoint:

```http
POST /diagnose
```

Admin diagnosis endpoint:

```http
POST /admin/diagnose
```

The public endpoint hides full retrieved content. The admin endpoint returns full retrieved source content and Agent trace events for debugging.

Example request:

```json
{
  "description": "我们公司最近增长放缓，团队每天都很忙，但新客户越来越少。管理层主要在抓成本和效率，员工只是完成 KPI。请帮我判断主要管理问题，并给出下一步建议。"
}
```

---

## Retrieval Evaluation

Eval data and experiment records are kept together:

```text
tests/evals/retrieval_cases.json
tests/evals/retrieval_experiments.jsonl
tests/evals/retrieval_experiments.md
```

Run retrieval eval:

```powershell
uv run python scripts\eval_retrieval.py
```

Record an experiment:

```powershell
uv run python scripts\eval_retrieval.py `
  --record-experiment `
  --experiment-name linear_015_085_candidates_5x25 `
  --notes "Selected default hybrid retrieval parameters."
```

Current selected retrieval setup:

```text
linear_015_085_candidates_5x25
```

Current recorded result:

```text
keyword   hit@3 0.375 | hit@5 0.438 | recall@5 0.167 | mrr@5 0.245
embedding hit@3 0.625 | hit@5 0.812 | recall@5 0.458 | mrr@5 0.481
hybrid    hit@3 0.562 | hit@5 0.812 | recall@5 0.438 | mrr@5 0.588
```

RRF hybrid retrieval is implemented and recorded as an experiment, but the current default remains linear hybrid because it performs better on the current eval set.

---

## Tests

Run all tests:

```powershell
uv run python -m pytest
```

---

## Project Structure

```text
app/
  agent/
  llm/
  memory/
  rag/
  schemas/
  tools/

scripts/

streamlit_app.py

tests/
  evals/
```
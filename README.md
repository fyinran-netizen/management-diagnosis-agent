# Management Diagnosis Agent

A local LangGraph + Ollama management diagnosis workflow exposed through Streamlit.

## Workflow

```text
Understanding -> Retrieval -> Generation -> Validation -> Persistence
```

Understanding checks clarity, detects language, routes problem types, and prepares diagnosis hints. Retrieval uses the existing BM25, embedding, linear hybrid (default), RRF experiment, and retrieval-quality checks. Generation owns report prompts and revision prompts. Validation applies report rules. Persistence stores diagnosis history and run metadata in `data/diagnosis_history/`.

LangGraph only coordinates these five stages and passes `AgentState`; the LLM is not used as an autonomous tool selector.

## Run

```powershell
uv run streamlit run streamlit_app.py
```

Ollama must be running for report generation. Configure `OLLAMA_BASE_URL`, `GENERATION_MODEL`, and `EMBEDDING_MODEL` in `.env`.

## Application logging

Streamlit initializes Python application logging at startup. Logs are written to the terminal and `.runtime/logs/application.log`. Set `APP_LOG_LEVEL` or `APP_LOG_FILE` in the environment to override the defaults. Application logs contain workflow/node summaries and timings, not full prompts, retrieved chunks, or user descriptions.

## Retrieval

The default remains linear hybrid retrieval with keyword weight `0.15`, embedding weight `0.85`, candidate multiplier `5`, and minimum candidates `25`. The local knowledge base and vector index are unchanged.

```powershell
uv run python scripts\build_vector_index.py
uv run python scripts\debug_retrieval.py "management problem" --top-k 3
uv run python scripts\eval_retrieval.py
```

## Tests

```powershell
uv run streamlit run streamlit_app.py
```

## Project structure

```text
app/
  agent/       # LangGraph workflow and state
  tools/       # understanding, retrieval, generation, validation, persistence
  llm/         # Ollama client only
  core/        # shared config and exceptions

scripts/
streamlit_app.py
tests/
```

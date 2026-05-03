# Management Diagnosis Agent

A local RAG-based management diagnosis agent prototype built with FastAPI, LangGraph, Ollama, and a local management knowledge base.

This project is designed as an AI Agent demo for management consulting and enterprise diagnosis scenarios. A user can provide an unstructured description of a company's current challenge, and the system will retrieve relevant management knowledge, generate a structured diagnosis report, verify the report quality, revise the report if needed, and save the diagnosis record into local memory.

---

## Current Implementation

The current version is a local prototype that has implemented:

- FastAPI backend service
- Local LLM integration through Ollama
- Qwen3 8B local model
- Keyword-based RAG over a sample management knowledge base
- LangGraph workflow orchestration
- Free-form user input through a single `description` field
- Automatic output language detection
- Problem routing based on management issue types
- Diagnosis hint generation
- Report generation using retrieved knowledge
- Rule-based report verification
- Revision loop when verification fails
- Local project memory storage

---

## Why This Is an Agent Demo

A basic chatbot usually follows this pattern:

```text
User input
→ LLM
→ Response
```

This project follows a workflow-based agent pattern:

```text
User description
→ Intake
→ Problem Routing
→ Knowledge Retrieval
→ Diagnosis Generation
→ Report Verification
→ Revision if needed
→ Memory Save
→ Final Response
```

The system does not only ask the LLM to answer directly. It first processes the user's input, retrieves relevant knowledge, generates a grounded report, checks whether the report is useful and complete, and stores the result for future use.

---

## Tech Stack

- Python
- FastAPI
- Uvicorn
- LangGraph
- Ollama
- Qwen3 8B local model
- Pydantic
- Keyword-based retrieval
- Local JSONL memory
- uv for environment and dependency management

---

## Project Structure

```text
management_diagnosis_agent/
│
├── app/
│   ├── main.py
│   │
│   ├── agent/
│   │   ├── graph.py
│   │   ├── state.py
│   │   ├── nodes.py
│   │   └── prompts.py
│   │
│   ├── llm/
│   │   └── ollama_client.py
│   │
│   ├── rag/
│   │   ├── chunker.py
│   │   ├── ingest.py
│   │   └── retriever.py
│   │
│   ├── tools/
│   │   ├── language_tool.py
│   │   ├── problem_router_tool.py
│   │   ├── diagnosis_tools.py
│   │   └── verify_tool.py
│   │
│   ├── memory/
│   │   └── project_memory.py
│   │
│   └── schemas/
│       ├── request.py
│       └── response.py
│
├── data/
│   ├── sample_knowledge_base/
│   ├── private_knowledge_base/
│   └── project_memory/
│
├── tests/
│
├── .env.example
├── .gitignore
├── pyproject.toml
├── uv.lock
└── README.md
```

---

## Internal Workflow and Tool Calls

The current agent workflow is implemented with LangGraph.

It can be understood as a state machine. Each node reads and updates the shared `AgentState`.

---

## High-level State Transition

```text
+----------------+
| START          |
+----------------+
        |
        v
+----------------+
| intake_node    |
+----------------+
        |
        v
+----------------+
| route_node     |
+----------------+
        |
        v
+----------------+
| retrieve_node  |
+----------------+
        |
        v
+----------------+
| generate_node  |
+----------------+
        |
        v
+----------------+
| verify_node    |
+----------------+
        |
        +-----------------------------+
        |                             |
        | passed = true               | passed = false
        v                             v
+----------------+           +----------------+
| memory_node    |           | revise_node    |
+----------------+           +----------------+
        |                             |
        v                             v
+----------------+           +----------------+
| END            | <---------| verify_node    |
+----------------+           +----------------+
```

Current revision rule:

```text
If verification fails and revision_count < MAX_REVISIONS:
    go to revise_node

Otherwise:
    go to memory_node
```

Currently:

```text
MAX_REVISIONS = 1
```

So the workflow allows at most one revision attempt.

---

## AgentState

The workflow passes a shared state object between nodes.

```text
+--------------------------------------------------+
| AgentState                                       |
+--------------------------------------------------+
| description                                      |
| company_context                                  |
| goal                                             |
| language                                         |
| problem_types                                    |
| diagnosis_hints                                  |
| retrieved_chunks                                 |
| report                                           |
| verification                                     |
| revision_count                                   |
| project_id                                       |
| final_answer                                     |
+--------------------------------------------------+
```

Each node reads part of the state and writes new fields back into it.

---

## Node-by-node Explanation

### 1. intake_node

```text
+--------------------------------------------------+
| intake_node                                      |
+--------------------------------------------------+
| Input state fields:                              |
| - description                                    |
|                                                  |
| Calls tools:                                     |
| - detect_output_language()                       |
|                                                  |
| Output state fields:                             |
| - company_context                                |
| - goal                                           |
| - language                                       |
+--------------------------------------------------+
```

Purpose:

```text
Convert the user's raw free-form description into internal fields used by later nodes.
```

Current behavior:

```text
description
→ company_context
→ default goal
→ detected output language
```

Example:

```text
User description:
"我们公司最近增长放缓，员工目标混乱，请帮我做诊断。"

intake_node output:
company_context = original description
goal = default diagnosis goal
language = zh
```

---

### 2. route_node

```text
+--------------------------------------------------+
| route_node                                       |
+--------------------------------------------------+
| Input state fields:                              |
| - company_context                                |
| - goal                                           |
|                                                  |
| Calls tools:                                     |
| - route_problem()                                |
| - build_diagnosis_hints()                        |
|                                                  |
| Output state fields:                             |
| - problem_types                                  |
| - diagnosis_hints                                |
+--------------------------------------------------+
```

Purpose:

```text
Classify the user's messy business problem into clearer management issue types.
```

Example output:

```text
problem_types:
- customer_value_misalignment
- metrics_misalignment
- opportunity_neglect
- control_over_self_drive
```

The diagnosis hints are then generated based on these problem types.

---

### 3. retrieve_node

```text
+--------------------------------------------------+
| retrieve_node                                    |
+--------------------------------------------------+
| Input state fields:                              |
| - company_context                                |
| - goal                                           |
| - problem_types                                  |
| - diagnosis_hints                                |
|                                                  |
| Calls tools:                                     |
| - retrieve_relevant_chunks()                     |
|                                                  |
| Output state fields:                             |
| - retrieved_chunks                               |
+--------------------------------------------------+
```

Purpose:

```text
Retrieve relevant knowledge chunks from the local knowledge base.
```

Current retrieval method:

```text
keyword-based retrieval
```

Current knowledge source:

```text
data/sample_knowledge_base/
```

Example output:

```json
[
  {
    "source": "01_customer_value.md",
    "title": "Common Symptoms",
    "content": "...",
    "score": 31
  },
  {
    "source": "04_metrics.md",
    "title": "Common Symptoms",
    "content": "...",
    "score": 23
  }
]
```

---

### 4. generate_node

```text
+--------------------------------------------------+
| generate_node                                    |
+--------------------------------------------------+
| Input state fields:                              |
| - company_context                                |
| - goal                                           |
| - language                                       |
| - problem_types                                  |
| - diagnosis_hints                                |
| - retrieved_chunks                               |
|                                                  |
| Calls tools / functions:                         |
| - build_generation_messages()                    |
| - chat_with_ollama()                             |
|                                                  |
| Output state fields:                             |
| - report                                         |
| - revision_count                                 |
+--------------------------------------------------+
```

Purpose:

```text
Generate the first structured management diagnosis report.
```

The prompt is built from:

```text
user description
+ detected problem types
+ diagnosis hints
+ retrieved knowledge chunks
```

Then the prompt is sent to the local Ollama model.

Current model:

```text
qwen3:8b
```

---

### 5. verify_node

```text
+--------------------------------------------------+
| verify_node                                      |
+--------------------------------------------------+
| Input state fields:                              |
| - report                                         |
| - retrieved_chunks                               |
|                                                  |
| Calls tools:                                     |
| - verify_report_quality()                        |
|                                                  |
| Output state fields:                             |
| - verification                                   |
+--------------------------------------------------+
```

Purpose:

```text
Check whether the generated report is complete, grounded, and useful.
```

Current verification checks:

```text
- report is not empty
- report is not too short
- report includes practical recommendations
- report includes assumptions or missing information
- report references retrieved knowledge sources
- report does not contain word count or length notes
- report does not appear truncated
- brackets and quotation marks are not obviously unmatched
```

Example pass result:

```json
{
  "passed": true,
  "issues": [],
  "needs_revision": false
}
```

Example fail result:

```json
{
  "passed": false,
  "issues": [
    "The report does not include clear practical recommendations.",
    "The report does not clearly separate assumptions or missing information."
  ],
  "needs_revision": true
}
```

---

### 6. revise_node

```text
+--------------------------------------------------+
| revise_node                                      |
+--------------------------------------------------+
| Input state fields:                              |
| - company_context                                |
| - goal                                           |
| - language                                       |
| - retrieved_chunks                               |
| - report                                         |
| - verification                                   |
| - revision_count                                 |
|                                                  |
| Calls tools / functions:                         |
| - build_revision_messages()                      |
| - chat_with_ollama()                             |
|                                                  |
| Output state fields:                             |
| - report                                         |
| - revision_count                                 |
+--------------------------------------------------+
```

Purpose:

```text
Revise the report based on verification issues.
```

Example:

```text
If verify_node says:
"The report does not include clear practical recommendations."

revise_node asks the LLM to rewrite the report and add practical recommendations.
```

Current behavior:

```text
revision_count increases by 1
```

---

### 7. memory_node

```text
+--------------------------------------------------+
| memory_node                                      |
+--------------------------------------------------+
| Input state fields:                              |
| - company_context                                |
| - goal                                           |
| - retrieved_chunks                               |
| - verification                                   |
| - revision_count                                 |
| - report                                         |
|                                                  |
| Calls tools:                                     |
| - save_project_record()                          |
|                                                  |
| Output state fields:                             |
| - project_id                                     |
| - final_answer                                   |
+--------------------------------------------------+
```

Purpose:

```text
Save the final diagnosis result into local project memory.
```

Current memory storage:

```text
data/project_memory/records.jsonl
```

This directory is ignored by Git.

Example saved fields:

```text
project_id
created_at
company_context
goal
retrieved_sources
verification
revision_count
final_answer_preview
```

---

## Full Tool Call Map

```text
+-------------------+---------------------------------------------+
| Node              | Tool / Function Called                      |
+-------------------+---------------------------------------------+
| intake_node       | detect_output_language()                    |
| route_node        | route_problem(); build_diagnosis_hints()                     |
| retrieve_node     | retrieve_relevant_chunks()                  |
| generate_node     | build_generation_messages(); chat_with_ollama()                          |
| verify_node       | verify_report_quality()                     |
| revise_node       | build_revision_messages(); chat_with_ollama()                          |
| memory_node       | save_project_record()                       |
+-------------------+---------------------------------------------+
```

---

## Current Workflow Type

The current project is a workflow-based agent.

It is not a fully autonomous agent where the LLM freely chooses every next step.

Instead, it uses a controlled workflow:

```text
fixed main path
+ conditional verification branch
+ limited revision loop
+ local memory persistence
```

This design is more stable for a first agent demo.

---

## API Usage

### Start the backend

```bash
uv run uvicorn app.main:app --reload
```

Then open:

```text
http://127.0.0.1:8000/docs
```

---

### Health Check

```http
GET /health
```

Response:

```json
{
  "status": "ok"
}
```

---

### Diagnose Management Problem

```http
POST /diagnose
```

Request:

```json
{
  "description": "我们公司最近增长放缓，团队每天都很忙，但新客户越来越少。管理层现在主要在抓成本和效率，员工觉得目标越来越乱，很多人只是在完成KPI。请帮我判断主要管理问题，并给出下一步建议。"
}
```

Response example:

```json
{
  "model": "qwen3:8b",
  "diagnosis_report": "...",
  "retrieved_sources": [
    {
      "source": "01_customer_value.md",
      "title": "Common Symptoms",
      "content": "...",
      "score": 31
    }
  ],
  "verification": {
    "passed": true,
    "issues": [],
    "needs_revision": false
  },
  "revision_count": 0,
  "project_id": "..."
}
```

---

## Knowledge Base Design

The project currently uses a small sample knowledge base for demonstration.

```text
data/sample_knowledge_base/
```

The real private manuscript should be placed under:

```text
data/private_knowledge_base/
```

This directory is ignored by Git and should not be uploaded to GitHub.

Current sample knowledge files include:

```text
01_customer_value.md
02_opportunity.md
03_strategy_organization.md
04_metrics.md
05_self_drive.md
```

Each file follows a structured format:

```text
# Topic Title

## Core Idea

## Common Symptoms

## Diagnostic Questions

## Suggested Actions
```

This structure makes retrieval easier and helps the model generate more grounded management diagnosis reports.

---

## Private Knowledge Base

The private management manuscript is not included in this repository.

The repository only includes sample knowledge files for demonstration purposes.

Ignored local directories:

```text
data/private_knowledge_base/
data/project_memory/
data/chroma_db/
```

---

## Current Limitations

The current version is still a prototype.

Known limitations:

- Retrieval is keyword-based, not embedding-based yet.
- The sample knowledge base is still small.
- The verification tool is rule-based and not yet a full semantic evaluator.
- Memory is currently used for saving records, but not yet for continuing previous projects.
- The workflow is mostly fixed, not fully dynamic.
- There is no frontend yet.
- There is no evaluation dataset yet.

---

## Roadmap

### Short-term

- Improve README and tests
- Process the private management manuscript into structured markdown
- Make keyword RAG work with the private knowledge base
- Improve prompts for more stable consulting-style reports
- Add simple evaluation cases

### Medium-term

- Upgrade keyword retrieval to embedding-based retrieval
- Add hybrid search combining keyword and embedding retrieval
- Add source-grounding verification
- Add clarification node when user input is too vague
- Let memory support follow-up diagnosis using `project_id`

### Long-term

- Add reranking
- Add more specialized diagnosis tools
- Add a simple frontend
- Add tracing and node-level logging
- Add a more production-like vector database
- Support more advanced agentic decision-making

---

## Current Agent Capabilities

The current prototype demonstrates:

- Local LLM integration
- RAG-based knowledge grounding
- Workflow orchestration with LangGraph
- Tool-based language detection
- Tool-based problem routing
- Tool-based diagnosis hints
- Rule-based Agent Verify
- Revision loop
- Local memory persistence
- Private knowledge base separation

This makes it a basic but complete local AI Agent workflow demo for management diagnosis.
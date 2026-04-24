# 🤖 Phase 3: Agentic RAG Pipeline (Production-Grade) - Multi-Agent, Stateful, Observable RAG

`rag-agent-v3` is a production-style Retrieval-Augmented Generation system with:

- FastAPI backend (`app/main.py`)
- LangGraph multi-agent orchestration (`app/graph.py`, `app/nodes.py`)
- Qdrant vector retrieval + Docling ingestion + BGE-Reranker (`app/engine.py`)
- Redis checkpointed conversation memory
- PostgreSQL permanent telemetry database
- Streamlit frontend with SSE streaming (`frontend/streamlit_app.py`)
- DeepEval background faithfulness checks + Phoenix tracing

### ✅ Phase 3 is Complete. This repository currently features:

- **Step 1:** Supervisor hub-and-spoke routing (Policy-Based Routing)
- **Step 2:** History-aware query condensation (Pronoun & Context Resolution)
- **Step 3:** Two-Stage Retrieval (Top-10 Qdrant -> Top-4 `BAAI/bge-reranker-base` + "Goldilocks" Grader)
- **Step 4:** Rolling History Summarization (Context Window Diet / Buffer Memory)
- **Step 5:** Telemetry persistence to PostgreSQL (Enterprise Tracing)
- **Reliability Hardening:** No-context fallback for low-grounding answers, model pre-warming for instant inference, and strict token limits.

---

## Architecture Overview

### Core Components

- `FastAPI`: API surface for ingestion, chat, and history.
- `LangGraph`: Stateful graph with conditional routing and memory management.
- `Qdrant & FastEmbed`: Vector store and fast embedding for document chunks.
- `CrossEncoder (BGE-Reranker)`: Stage 2 retrieval refinement to maximize precision.
- `Redis`: Chat/session checkpoint state (`thread_id` based).
- `PostgreSQL`: Permanent ACID-compliant storage for Phoenix spans, traces, and metrics.
- `Streamlit`: User interface and token streaming display.
- `DeepEval`: Asynchronous faithfulness scoring after response generation.
- `Arize Phoenix`: Tracing and observability via OpenTelemetry.

### Current Graph Flow (Phase 3)

1. `condense_query`: Rewrites follow-up user messages into standalone search intent using active memory.
2. `supervisor_route`: Dynamically selects via policy:
   - `document_agent`: For grounded/factual/indexed-knowledge questions.
   - `conversational_agent`: For pure greetings/light chat (bypasses RAG).
3. **Document Path (Two-Stage):**
   - `retrieve_docs` -> Fetches Top 10 chunks from Qdrant, reranks to Top 4 via BGE-Reranker.
   - `grade_documents` -> Evaluates relevance using a lenient pronoun/strict fact policy.
   - if relevant -> `generate_answer`.
   - else -> `rewrite_query` loop (bounded).
   - if still irrelevant at loop limit -> `no_context_fallback`.
4. **Conversational Path:**
   - `conversational_agent` returns non-grounded responses directly.
5. **Memory Manager:**
   - `summarize_memory` runs at the end of the graph. If history exceeds 4 messages, it compresses older messages into a rolling summary to protect the LLM context window.
6. **Telemetry:**
   - Background task runs DeepEval for completed answers and permanently exports all telemetry/spans to PostgreSQL via Phoenix.

---

## Prerequisites

Install these first:

- Python `3.10+` (recommended: `3.11`)
- Docker Desktop (with Docker Compose)
- Ollama
- Git

Optional but recommended:
- RedisInsight (exposed via docker-compose)
- DBeaver / pgAdmin (to view PostgreSQL data)
- Postman or curl for API testing

---

## Quick Start (Fresh Setup)

### 1) Clone and enter repository

```bash
git clone <your-repo-url>
cd rag-agent-v3
2) Create and activate virtual environment
Windows PowerShell:

PowerShell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
macOS/Linux:

Bash
python3 -m venv .venv
source .venv/bin/activate
3) Install Python dependencies
Bash
pip install --upgrade pip
pip install -r requirements.txt
4) Pull local model in Ollama
Bash
ollama pull llama3.1:8b
5) Start infrastructure services
Bash
docker-compose up -d
Services Running:

Qdrant: http://localhost:6333

Phoenix UI (Tracing): http://localhost:6006

RedisInsight UI: http://localhost:8001

Redis (State): localhost:6379

PostgreSQL (Telemetry): localhost:5432

6) Start backend API
Bash
python app/main.py
Backend URLs:

API base: http://localhost:8080

Swagger: http://localhost:8080/docs

7) Start Streamlit frontend (new terminal, same venv)
Bash
streamlit run frontend/streamlit_app.py
Frontend URL:

http://localhost:8501

Environment and Configuration
This project currently reads key settings from environment variables in code defaults.
If you want custom behavior, set these before startup:

QDRANT_HOST (default: localhost)

QDRANT_PORT (default: 6333)

COLLECTION_NAME (default: pdf_docs)

EMBED_MODEL (default: BAAI/bge-m3)

No .env file is required by default, but python-dotenv loading is supported in app/database.py.

API Reference
1) Ingest Document
POST /v2/ingest/file

Request:

JSON
{
  "file_path": "C:/absolute/path/to/document.pdf",
  "metadata": {
    "category": "resume"
  }
}
Response:

JSON
{
  "status": "success",
  "chunks_indexed": 42
}
2) Chat with Agent
POST /v2/agent/chat

Request:

JSON
{
  "question": "Tell me the education details from the resume",
  "thread_id": "user_session_1"
}
Response is an SSE stream with token events (type: token) and a metadata event (type: metadata, includes sources).

3) Retrieve Chat History
GET /v2/agent/history/{thread_id}

Returns reconstructed user/assistant messages from Redis checkpoints, allowing frontend clients to seamlessly restore context on reload.

Project Structure
app/main.py - FastAPI app, SSE streaming, background eval, history endpoint (with Reranker pre-warming)

app/graph.py - LangGraph topology and routing edges

app/nodes.py - Condensation, supervisor, retrieval, grading, generation, summarization, and fallback

app/schemas.py - API/state schemas and structured output contracts

app/engine.py - Docling ingestion and Qdrant/BGE-Reranker logic

app/database.py - Qdrant client initialization and collection checks

app/evaluator.py - DeepEval faithfulness logic

app/observability.py - Phoenix/OpenTelemetry instrumentation

app/llm.py - Ollama model configuration

frontend/streamlit_app.py - Streamlit client, history restoration, and stream rendering

docker-compose.yml - Qdrant, Redis, RedisInsight, PostgreSQL, Phoenix services

Troubleshooting
Streamlit shows blank response for some turns
Ensure backend emits fallback token from final state when no model stream is produced.

Confirm /v2/agent/chat stream includes token and metadata events.

Document exists but answer says "not found"
Verify the document doesn't contain heavy placeholder text (e.g., Lorem Ipsum) which may trigger Grader rejection.

Test with a fresh thread_id.

First request takes 1-2 minutes locally
Ensure the BGE-Reranker pre-warming logic in main.py is executing successfully during server startup.

Redis history appears stale / UI resets on reload
Ensure streamlit_app.py makes a GET request to the history endpoint upon initialization.

If migrating environments, ensure your Docker volume (redis_data) mapped correctly. Switch to a new thread_id for clean tests.

Development Notes
This repo is intentionally built as a modular platform for future autonomous workflows.
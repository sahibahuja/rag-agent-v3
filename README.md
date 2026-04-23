# RAG Agent v3 - Multi-Agent, Stateful, Observable RAG

`rag-agent-v3` is a production-style Retrieval-Augmented Generation system with:

- FastAPI backend (`app/main.py`)
- LangGraph multi-agent orchestration (`app/graph.py`, `app/nodes.py`)
- Qdrant vector retrieval + Docling ingestion (`app/engine.py`)
- Redis checkpointed conversation memory
- Streamlit frontend with SSE streaming (`frontend/streamlit_app.py`)
- DeepEval background faithfulness checks + Phoenix tracing

This repository currently contains:

- Phase 3 Step 1: Supervisor hub-and-spoke routing
- Phase 3 Step 2: History-aware query condensation
- Reliability hardening: no-context fallback for low-grounding answers

---

## Architecture Overview

### Core Components

- `FastAPI`: API surface for ingestion, chat, and history.
- `LangGraph`: stateful graph with conditional routing.
- `Qdrant`: vector store for document chunks.
- `Redis`: chat/session checkpoint state (`thread_id` based).
- `Streamlit`: user interface and token streaming display.
- `DeepEval`: asynchronous faithfulness scoring after response generation.
- `Arize Phoenix`: tracing and observability via OpenTelemetry.

### Current Graph Flow (Phase 3)

1. `condense_query` rewrites follow-up user messages into standalone search intent.
2. `supervisor_route` selects:
   - `document_agent` for grounded/factual/indexed-knowledge questions
   - `conversational_agent` for greetings/light chat
3. Document path:
   - `retrieve_docs` -> `grade_documents`
   - if relevant -> `generate_answer`
   - else -> `rewrite_query` loop (bounded)
   - if still irrelevant at loop limit -> `no_context_fallback`
4. Conversational path:
   - `conversational_agent` returns response directly.
5. Background task runs DeepEval for completed answer.

---

## Prerequisites (New Machine)

Install these first:

- Python `3.10+` (recommended: `3.11`)
- Docker Desktop (with Docker Compose)
- Ollama
- Git

Optional but recommended:

- RedisInsight (already exposed via docker-compose)
- Postman or curl for API testing

---

## Quick Start (Fresh Setup)

### 1) Clone and enter repository

```bash
git clone <your-repo-url>
cd rag-agent-v3
```

### 2) Create and activate virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3) Install Python dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4) Pull local model in Ollama

```bash
ollama pull llama3.1:8b
```

### 5) Start infrastructure services

```bash
docker-compose up -d
```

Services:

- Qdrant: `http://localhost:6333`
- Phoenix UI: `http://localhost:6006`
- RedisInsight UI: `http://localhost:8001`
- Redis: `localhost:6379`

### 6) Start backend API

```bash
python app/main.py
```

Backend URLs:

- API base: `http://localhost:8080`
- Swagger: `http://localhost:8080/docs`

### 7) Start Streamlit frontend (new terminal, same venv)

```bash
streamlit run frontend/streamlit_app.py
```

Frontend URL:

- `http://localhost:8501`

---

## Environment and Configuration

This project currently reads key settings from environment variables in code defaults.
If you want custom behavior, set these before startup:

- `QDRANT_HOST` (default: `localhost`)
- `QDRANT_PORT` (default: `6333`)
- `COLLECTION_NAME` (default: `pdf_docs`)
- `EMBED_MODEL` (default: `BAAI/bge-m3`)

No `.env` file is required by default, but `python-dotenv` loading is supported in `app/database.py`.

---

## API Reference

### 1) Ingest Document

`POST /v2/ingest/file`

Request:

```json
{
  "file_path": "C:/absolute/path/to/document.pdf",
  "metadata": {
    "category": "resume"
  }
}
```

Response:

```json
{
  "status": "success",
  "chunks_indexed": 42
}
```

### 2) Chat with Agent

`POST /v2/agent/chat`

Request:

```json
{
  "question": "Tell me the education details from the resume",
  "thread_id": "user_session_1"
}
```

Response is SSE stream with:

- token events (`type: token`)
- metadata event (`type: metadata`, includes `sources`)

### 3) Retrieve Chat History

`GET /v2/agent/history/{thread_id}`

Returns reconstructed user/assistant messages from Redis checkpoints.

---

## Project Structure

- `app/main.py` - FastAPI app, SSE streaming, background eval, history endpoint
- `app/graph.py` - LangGraph topology and routing edges
- `app/nodes.py` - condensation, supervisor, retrieval, grading, rewrite, generation, fallback
- `app/schemas.py` - API/state schemas and structured output contracts
- `app/engine.py` - Docling ingestion and Qdrant retrieval helpers
- `app/database.py` - Qdrant client initialization and collection checks
- `app/evaluator.py` - DeepEval faithfulness logic
- `app/observability.py` - Phoenix/OpenTelemetry instrumentation
- `app/llm.py` - Ollama model configuration
- `frontend/streamlit_app.py` - Streamlit client and stream rendering
- `docker-compose.yml` - Qdrant, Redis, RedisInsight, Phoenix services

---

## Troubleshooting

### Streamlit shows blank response for some turns

- Ensure backend emits fallback token from final state when no model stream is produced.
- Confirm `/v2/agent/chat` stream includes `token` and `metadata` events.

### Document exists but answer says "not found"

- Re-ingest the correct document path.
- Test with a fresh `thread_id`.
- Increase retrieval limit temporarily for debugging.
- Verify retrieved chunks/logs include expected section text.

### Phoenix fails to start (port bind)

- Check if configured port is already in use.
- Avoid conflicting env overrides for `PHOENIX_GRPC_PORT`.

### Redis history appears stale

- Switch to a new `thread_id` for clean tests.
- Optionally clear keys via RedisInsight.

---

## Development Notes

- This repo is intentionally built as a modular platform for future autonomous workflows.
- Current roadmap target includes:
  - Step 3: cross-encoder reranking
  - Step 4: rolling history summarization
  - Step 5: telemetry persistence to PostgreSQL

---

## License

Add your preferred license file (`LICENSE`) if this project will be shared publicly.
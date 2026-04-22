# Phase 3 Architecture Roadmap: Multi-Agent RAG System

## Current State (Phase 2)
- Built on LangGraph & FastAPI.
- Uses Redis for state checkpointer memory.
- Uses DeepEval for background asynchronous evaluation.
- Streamlit UI with Server-Sent Events (SSE) streaming and downloadable sources.

## Phase 3 Goal
Refactor the monolithic graph into a Hub-and-Spoke Multi-Agent Supervisor framework.

## Step-by-Step Execution Plan
1. **The Supervisor Refactor:** Upgrade `AgentState` to include `next_active_agent`. Create a Supervisor LLM node to route traffic between a `document_agent` (heavy RAG) and a `conversational_agent` (lightweight chat).
2. **Hybrid Query Condensation:** Add a fast LLM node *before* the Supervisor to rewrite conversational pronouns ("summarize it") into standalone queries.
3. **Context Window Diet:** Inject a Cross-Encoder Reranker (`bge-reranker`) into the Document Agent to strictly prune low-relevance chunks.
4. **Rolling History Buffer:** Add a background node to summarize Redis history if the conversation exceeds 4 messages.
5. **Telemetry DB:** Export DeepEval scores and traces to PostgreSQL for future fine-tuning.
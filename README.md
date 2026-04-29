# 🤖 Enterprise Agentic RAG Pipeline - Multi-Tenant, Stateful, Observable

`rag-agent-v3` is a production-grade Retrieval-Augmented Generation (RAG) architecture designed for scalability, data security, and autonomous routing.

Built for enterprise environments, this system features hard multi-tenancy at the vector database level, persistent time-travel state management, and asynchronous telemetry.

---

## 🏗️ System Architecture & Data Flow

The following diagram illustrates the lifecycle of a user request through the multi-agent system:

```mermaid
graph TD
    %% UI Layer
    A[User / Streamlit UI] -->|SSE Payload w/ tenant_id & thread_id| B(FastAPI Gateway)

    %% API & Graph Entry
    B -->|Injects tenant_id| C{LangGraph StateManager}
    C --> D[Condense Query Node]

    %% Supervisor Routing
    D --> E{Supervisor Agent}
    E -->|Casual Chat| F[Conversational Agent]
    E -->|Factual Query| G[Retrieve Docs Node]

    %% Retrieval Engine (The Security Wall)
    G -->|Applies tenant_id Filter| H[(Qdrant Vector DB)]
    H -->|Stage 1: FastEmbed BGE-M3| G
    G -->|Stage 2: BAAI CrossEncoder| I[Rerank & Merge Parent Chunks]

    %% Evaluation & Generation
    I --> J[Grade Documents Node]
    J -->|Irrelevant| K[Rewrite Query]
    K --> G
    J -->|Relevant| L[Generate Answer Node]

    %% Memory & Telemetry
    F --> M[Summarize Memory Node]
    L --> M
    M -->|Checkpoint State| N[(Redis)]
    M --> O[Stream Response to UI]

    %% Async Observability
    O -.->|Background Task| P[DeepEval Faithfulness]
    P -.-> Q[(PostgreSQL / Phoenix)]
🧠 Architecture Decision Records (ADRs) - The "Why"This system implements several advanced architectural patterns to solve common RAG failure points:1. Hard Multi-Tenancy via Payload Filtering (Data Security)Problem: In a multi-user environment, Tenant A's LLM prompt might accidentally retrieve Tenant B's sensitive documents.Solution: The system enforces a mathematical "Security Wall." A tenant_id is injected into the GraphState at the API gateway. Qdrant applies a strict FieldCondition payload filter during retrieval, ensuring 0% cross-tenant data leakage, regardless of prompt manipulation.2. Parent-Child Chunking Strategy (Context vs. Searchability)Problem: Small document chunks are great for exact-match searching, but terrible for providing the LLM enough context to answer complex questions.Solution: Documents are ingested using a Parent-Child strategy. Qdrant indexes small 600-character "Child" chunks for high-precision semantic search. During retrieval, the engine intercepts the result, maps it to its UUID, and swaps it with the larger 3000-character "Parent" chunk before sending it to the LLM.3. The "Context Diet" (Rolling Buffer Memory)Problem: Long conversations cause the LLM context window to overflow, increasing latency and hallucination rates.Solution: A dedicated summarize_memory node sits at the end of the graph. It maintains a strict "diet": only the last 4 messages are kept verbatim. Any older messages are compressed into a rolling summary paragraph by a background LLM call.4. Policy-Based Supervisor RoutingProblem: Forcing all user queries through a Vector DB wastes compute and causes awkward answers to simple greetings like "Hello."Solution: A Supervisor Agent evaluates the condensed query against strict routing policies. It routes grounded questions to the document_agent and casual/follow-up questions to the conversational_agent, bypassing the RAG pipeline entirely when unnecessary.5. Asynchronous ObservabilityProblem: Running RAG Evaluation (DeepEval) synchronously blocks the UI, causing massive latency for the end-user.Solution: DeepEval faithfulness checks and Arize Phoenix OpenTelemetry tracing are offloaded to FastAPI BackgroundTasks. The user receives their streaming response instantly, while the system grades the answer in the background and commits the trace to an ACID-compliant PostgreSQL database.🛠️ Tech Stack & JustificationComponentTechnologyJustificationBackend / APIFastAPIAsync-first, high throughput, native Server-Sent Events (SSE) support.OrchestrationLangGraphState-machine based routing, cyclical loops, and native Redis integration.Vector DatabaseQdrantHigh-performance Rust-based engine, supports hard payload filtering.EmbeddingsFastEmbed (BGE-M3)Local execution, CPU-optimized, no external API latency.RerankingBAAI/bge-reranker-baseStage-2 CrossEncoder to maximize top-k retrieval precision.IngestionDoclingSuperior handling of complex PDFs, tables, and OCR compared to PyPDF.State / MemoryRedisHigh-speed, persistent key-value store for LangGraph thread checkpoints.TelemetryArize Phoenix + PostgreSQLOpenTelemetry standard, persistent trace storage across container restarts.EvaluationDeepEvalLLM-as-a-judge metric scoring (Faithfulness, Answer Relevance).FrontendStreamlitRapid prototyping, native chat UI components, Python-native.🚀 Quick Start & DeploymentPrerequisitesPython 3.10+ (recommended: 3.11)Docker Desktop (with Docker Compose)Ollama (running locally with llama3.1:8b pulled)1. Start InfrastructureBoot up the required databases and telemetry services.Bashdocker-compose up -d
Services Running:Qdrant: localhost:6333Phoenix UI: localhost:6006RedisInsight: localhost:8001PostgreSQL: localhost:54322. Environment SetupBashpython -m venv .venv
source .venv/bin/activate  # On Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
3. Start Application ServicesStart the FastAPI backend (Terminal 1):Bashpython app/main.py
Start the Streamlit UI (Terminal 2):Bashstreamlit run frontend/streamlit_app.py
📡 API Reference1. Ingest Document (Tenant Secured)POST /v2/ingest/fileJSON{
  "file_path": "C:/absolute/path/to/document.pdf",
  "metadata": { "category": "resume" },
  "tenant_id": "tenant_a"
}
2. Chat with Agent (Tenant Secured)POST /v2/agent/chatJSON{
  "question": "Tell me the education details from the resume",
  "tenant_id": "tenant_a",
  "thread_id": "user_session_1"
}
Returns an SSE stream yielding type: token and type: metadata events.3. Retrieve Checkpointed HistoryGET /v2/agent/history/{thread_id}Time-travels through Redis to reconstruct the full UI history based on the thread ID.Developed for advanced autonomous AI engineering workflows.
```

# Graph Report - rag-agent-v3  (2026-04-28)

## Corpus Check
- 12 files · ~5,706 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 71 nodes · 87 edges · 12 communities detected
- Extraction: 79% EXTRACTED · 21% INFERRED · 0% AMBIGUOUS · INFERRED: 18 edges (avg confidence: 0.7)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]

## God Nodes (most connected - your core abstractions)
1. `OllamaDeepEval` - 8 edges
2. `get_client()` - 6 edges
3. `test_parent_child()` - 5 edges
4. `init_db()` - 5 edges
5. `get_context_from_qdrant()` - 5 edges
6. `StorePayload` - 5 edges
7. `ChatPayload` - 5 edges
8. `ChatResponse` - 5 edges
9. `process_file()` - 4 edges
10. `check_faithfulness()` - 4 edges

## Surprising Connections (you probably didn't know these)
- `init_db()` --calls--> `lifespan()`  [INFERRED]
  app\database.py → app\main.py
- `get_reranker()` --calls--> `lifespan()`  [INFERRED]
  app\engine.py → app\main.py
- `process_file()` --calls--> `ingest_file()`  [INFERRED]
  app\engine.py → app\main.py
- `get_context_from_qdrant()` --calls--> `retrieve_docs()`  [INFERRED]
  app\engine.py → app\nodes.py
- `check_faithfulness()` --calls--> `run_background_eval()`  [INFERRED]
  app\evaluator.py → app\main.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.24
Nodes (10): get_client(), init_db(), Returns a single instance of the Qdrant client.      Initialization happens onl, Ensures the collection exists and handles dimension safety checks, get_context_from_qdrant(), get_reranker(), process_file(), rerank_results() (+2 more)

### Community 2 - "Community 2"
Cohesion: 0.18
Nodes (9): get_history(), ingest_file(), lifespan(), Time-travels through Redis to reconstruct the entire chat history      for a sp, Runs DeepEval as an independent trace, linked by Correlation ID, run_background_eval(), setup_tracing(), Payload for indexing new documents via Docling (+1 more)

### Community 3 - "Community 3"
Cohesion: 0.22
Nodes (4): check_faithfulness(), OllamaDeepEval, Called by the Background Task.     Now that the Pydantic cage is gone, DeepEval, DeepEvalBaseLLM

### Community 4 - "Community 4"
Cohesion: 0.5
Nodes (4): Routing logic: Where should the question go?, RouteQuery, SupervisorRoute, BaseModel

### Community 5 - "Community 5"
Cohesion: 0.5
Nodes (3): CondensedQuery, GraphState, TypedDict

### Community 6 - "Community 6"
Cohesion: 1.0
Nodes (2): FaithfulnessSchema, Judge logic: Did the AI hallucinate?

### Community 7 - "Community 7"
Cohesion: 1.0
Nodes (2): Message, Standard message format for history (OpenAI compatible)

### Community 8 - "Community 8"
Cohesion: 1.0
Nodes (2): GradeSchema, Relevance check: Is the document useful?

### Community 9 - "Community 9"
Cohesion: 1.0
Nodes (2): ChatPayload, Payload for the Agentic Chat endpoint

### Community 10 - "Community 10"
Cohesion: 1.0
Nodes (2): ChatResponse, Structured response for the final API output

### Community 15 - "Community 15"
Cohesion: 1.0
Nodes (1): Returns a single instance of the Qdrant client.      Initialization happens onl

### Community 16 - "Community 16"
Cohesion: 1.0
Nodes (1): Ensures the collection exists and handles dimension safety checks

## Knowledge Gaps
- **12 isolated node(s):** `Returns a single instance of the Qdrant client.      Initialization happens onl`, `Ensures the collection exists and handles dimension safety checks`, `Called by the Background Task.     Now that the Pydantic cage is gone, DeepEval`, `Payload for indexing new documents via Docling`, `Standard message format for history (OpenAI compatible)` (+7 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 6`** (2 nodes): `FaithfulnessSchema`, `Judge logic: Did the AI hallucinate?`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 7`** (2 nodes): `Message`, `Standard message format for history (OpenAI compatible)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 8`** (2 nodes): `GradeSchema`, `Relevance check: Is the document useful?`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 9`** (2 nodes): `ChatPayload`, `Payload for the Agentic Chat endpoint`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 10`** (2 nodes): `ChatResponse`, `Structured response for the final API output`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 15`** (1 nodes): `Returns a single instance of the Qdrant client.      Initialization happens onl`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 16`** (1 nodes): `Ensures the collection exists and handles dimension safety checks`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `run_background_eval()` connect `Community 2` to `Community 3`?**
  _High betweenness centrality (0.365) - this node is a cross-community bridge._
- **Why does `lifespan()` connect `Community 2` to `Community 0`?**
  _High betweenness centrality (0.285) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `get_client()` (e.g. with `test_parent_child()` and `process_file()`) actually correct?**
  _`get_client()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `test_parent_child()` (e.g. with `init_db()` and `get_client()`) actually correct?**
  _`test_parent_child()` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `init_db()` (e.g. with `test_parent_child()` and `lifespan()`) actually correct?**
  _`init_db()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Returns a single instance of the Qdrant client.      Initialization happens onl`, `Ensures the collection exists and handles dimension safety checks`, `Called by the Background Task.     Now that the Pydantic cage is gone, DeepEval` to the rest of the system?**
  _12 weakly-connected nodes found - possible documentation gaps or missing edges._
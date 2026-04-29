# Graph Report - rag-agent-v3  (2026-04-29)

## Corpus Check
- 12 files · ~5,598 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 78 nodes · 87 edges · 12 communities detected
- Extraction: 79% EXTRACTED · 21% INFERRED · 0% AMBIGUOUS · INFERRED: 18 edges (avg confidence: 0.65)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]

## God Nodes (most connected - your core abstractions)
1. `OllamaDeepEval` - 8 edges
2. `get_client()` - 6 edges
3. `StorePayload` - 6 edges
4. `ChatPayload` - 6 edges
5. `ChatResponse` - 6 edges
6. `init_db()` - 4 edges
7. `get_context_from_qdrant()` - 4 edges
8. `check_faithfulness()` - 4 edges
9. `lifespan()` - 4 edges
10. `Runs DeepEval as an independent trace, linked by Correlation ID` - 4 edges

## Surprising Connections (you probably didn't know these)
- `wipe_database()` --calls--> `get_client()`  [INFERRED]
  app\wipe_db.py → app\database.py
- `check_faithfulness()` --calls--> `run_background_eval()`  [INFERRED]
  app\evaluator.py → app\main.py
- `get_client()` --calls--> `process_file()`  [INFERRED]
  app\database.py → app\engine.py
- `get_client()` --calls--> `get_context_from_qdrant()`  [INFERRED]
  app\database.py → app\engine.py
- `init_db()` --calls--> `lifespan()`  [INFERRED]
  app\database.py → app\main.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.15
Nodes (13): get_client(), init_db(), Returns a single instance of the Qdrant client.      Initialization happens onl, Ensures the collection exists and handles dimension safety checks, get_context_from_qdrant(), get_reranker(), process_file(), rerank_results() (+5 more)

### Community 1 - "Community 1"
Cohesion: 0.2
Nodes (13): CondensedQuery, FaithfulnessSchema, GradeSchema, GraphState, Message, Standard message format for history (OpenAI compatible), Routing logic: Where should the question go?, Relevance check: Is the document useful? (+5 more)

### Community 2 - "Community 2"
Cohesion: 0.22
Nodes (11): get_history(), Time-travels through Redis to reconstruct the entire chat history      for a sp, Time-travels through Redis to reconstruct the entire chat history      for a sp, Runs DeepEval as an independent trace, linked by Correlation ID, run_background_eval(), ChatPayload, ChatResponse, Payload for the Agentic Chat endpoint (+3 more)

### Community 4 - "Community 4"
Cohesion: 0.22
Nodes (4): check_faithfulness(), OllamaDeepEval, Called by the Background Task.     Now that the Pydantic cage is gone, DeepEval, DeepEvalBaseLLM

### Community 9 - "Community 9"
Cohesion: 1.0
Nodes (1): Standard message format for history (OpenAI compatible)

### Community 10 - "Community 10"
Cohesion: 1.0
Nodes (1): Payload for the Agentic Chat endpoint

### Community 11 - "Community 11"
Cohesion: 1.0
Nodes (1): Structured response for the final API output

### Community 12 - "Community 12"
Cohesion: 1.0
Nodes (1): Routing logic: Where should the question go?

### Community 13 - "Community 13"
Cohesion: 1.0
Nodes (1): Relevance check: Is the document useful?

### Community 14 - "Community 14"
Cohesion: 1.0
Nodes (1): Judge logic: Did the AI hallucinate?

### Community 15 - "Community 15"
Cohesion: 1.0
Nodes (1): Returns a single instance of the Qdrant client.      Initialization happens onl

### Community 16 - "Community 16"
Cohesion: 1.0
Nodes (1): Ensures the collection exists and handles dimension safety checks

## Knowledge Gaps
- **18 isolated node(s):** `Returns a single instance of the Qdrant client.      Initialization happens onl`, `Ensures the collection exists and handles dimension safety checks`, `Called by the Background Task.     Now that the Pydantic cage is gone, DeepEval`, `Payload for indexing new documents via Docling`, `Standard message format for history (OpenAI compatible)` (+13 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 9`** (1 nodes): `Standard message format for history (OpenAI compatible)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 10`** (1 nodes): `Payload for the Agentic Chat endpoint`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 11`** (1 nodes): `Structured response for the final API output`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 12`** (1 nodes): `Routing logic: Where should the question go?`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 13`** (1 nodes): `Relevance check: Is the document useful?`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 14`** (1 nodes): `Judge logic: Did the AI hallucinate?`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 15`** (1 nodes): `Returns a single instance of the Qdrant client.      Initialization happens onl`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 16`** (1 nodes): `Ensures the collection exists and handles dimension safety checks`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `run_background_eval()` connect `Community 2` to `Community 4`?**
  _High betweenness centrality (0.310) - this node is a cross-community bridge._
- **Why does `lifespan()` connect `Community 0` to `Community 2`?**
  _High betweenness centrality (0.247) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `get_client()` (e.g. with `process_file()` and `get_context_from_qdrant()`) actually correct?**
  _`get_client()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `StorePayload` (e.g. with `Runs DeepEval as an independent trace, linked by Correlation ID` and `Time-travels through Redis to reconstruct the entire chat history      for a sp`) actually correct?**
  _`StorePayload` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `ChatPayload` (e.g. with `Runs DeepEval as an independent trace, linked by Correlation ID` and `Time-travels through Redis to reconstruct the entire chat history      for a sp`) actually correct?**
  _`ChatPayload` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Returns a single instance of the Qdrant client.      Initialization happens onl`, `Ensures the collection exists and handles dimension safety checks`, `Called by the Background Task.     Now that the Pydantic cage is gone, DeepEval` to the rest of the system?**
  _18 weakly-connected nodes found - possible documentation gaps or missing edges._
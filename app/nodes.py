from typing import cast
from app.llm import llm
from app.engine import get_context_from_qdrant
from app.schemas import GraphState, RouteQuery, GradeSchema, SupervisorRoute, CondensedQuery

# --- 1. The Router Node (PILLAR 1) ---
# --- 1. The Router Node ---
def route_question(state: GraphState):
    print("--- NODE: ROUTING QUESTION ---")
    question = state.get("question", "")
    
    structured_llm_router = llm.with_structured_output(RouteQuery)
    
    response = cast(RouteQuery, structured_llm_router.invoke([
        ("system", "Route the user query. Use 'vector_store' for Document questions and 'chat_history' for greetings or memory."),
        ("human", question)
    ]))
    
    # 🚨 THE SAFETY NET 🚨
    # If the LLM goes rogue, default to Document search so the app doesn't crash
    if response.datasource not in ["vector_store", "chat_history"]:
        print(f"⚠️ Router hallucinated '{response.datasource}', defaulting to 'vector_store'")
        return "vector_store"
        
    print(f"DEBUG: Routing to -> {response.datasource}")
    return response.datasource

# --- 2. The Retrieval Node (PILLAR 4 Optimized + SOURCES) ---
def retrieve_docs(state: GraphState):
    print("--- NODE: RETRIEVING FROM QDRANT ---")
    search_query = state.get("search_query") or state.get("question", "")
    
    # Pillar 4: Generate 1 alternative query to save time
    system_msg = "Generate 1 alternative search query. Output ONLY the query text."
    response = llm.invoke([
        ("system", system_msg),
        ("human", f"Query: {search_query}")
    ])
    
    queries = [search_query, str(response.content).strip()]
    
    # 🚨 KEPT: Your source-tracking engine call
    context_str, sources = get_context_from_qdrant(queries, limit=3)
    
    return {"context": [context_str], "sources": sources}

# --- 3. The Grader Node (PILLAR 2 Structured) ---
def grade_documents(state: GraphState):
    print("--- NODE: GRADING RELEVANCE ---")
    structured_grader = llm.with_structured_output(GradeSchema)
    
    context = "\n\n".join(state.get("context", []))
    question = state.get("question", "")

    response = cast(GradeSchema, structured_grader.invoke([
        ("system", "You are a grader assessing relevance of a retrieved document to a user question. Answer 'yes' or 'no'."),
        ("human", f"Context: {context}\n\nQuestion: {question}")
    ]))
    
    grade = response.binary_score.lower().strip()
    print(f"--- GRADER RESULT: {grade} ---")
    
    return {"is_relevant": grade}

# 1. Define the Router (Conditional Logic for Loops)
def decide_to_generate(state: GraphState):
    print("--- DECIDING NEXT STEP ---")
    relevance = state.get("is_relevant", "no")
    count = state.get("iteration_count", 0)

    print(f"DEBUG: Current iteration: {count}, Relevance: {relevance}")

    if relevance == "yes":
        print("--- DECISION: GENERATE (Relevant) ---")
        return "generate"

    if count >= 2:
        print("--- DECISION: NO_CONTEXT_FALLBACK (Limit reached + still not relevant) ---")
        return "no_context"

    print("--- DECISION: REWRITE ---")
    return "rewrite"

# --- 5. The Rewriter Node ---
def rewrite_query(state: GraphState):
    print("--- NODE: REWRITING QUERY ---")
    question = state.get("question", "")
    history = state.get("history", [])
    current_count = state.get("iteration_count", 0)
    
    history_str = "\n".join(history) if history else "No previous conversation."
    system_msg = "You are a search optimizer. Output ONLY optimized search keywords based on history."
    
    response = llm.invoke([
        ("system", system_msg),
        ("human", f"History: {history_str}\n\nQuestion: {question}")
    ])

    clean_query = str(response.content).strip().split('\n')[-1].replace('"', '')
    return {
        "search_query": clean_query, 
        "iteration_count": current_count + 1
    }

# --- 6. The Generator Node (SOURCES RESTORED) ---
def generate_answer(state: GraphState):
    print("--- NODE: GENERATING ANSWER ---")
    context_list = state.get("context", [])
    context = "\n\n".join(context_list) if context_list else "No context found."
    question = state.get("question", "")
    
    # 🚨 KEPT: Pulling sources from the state
    sources = state.get("sources", [])
    
    history = state.get("history", [])
    history_str = "\n".join(history) if history else "No previous conversation."

    system_msg = (
        "You are a helpful assistant. "
        "Use CONTEXT for document facts and HISTORY for conversation questions."
    )
    
    response = llm.invoke([
        ("system", system_msg),
        ("human", f"History:\n{history_str}\n\nContext:\n{context}\n\nQuestion: {question}")
    ])

    # 🚨 KEPT: Returning 'sources' in the final payload
    return {
        "response": str(response.content), 
        "sources": sources,
        "history": [f"User: {question}", f"AI: {response.content}"]
    }

# ---7. Supervisor Node
def supervisor_route(state: GraphState):
    print("--- NODE: SUPERVISOR ROUTING ---")

    raw_question = str(state.get("question", "")).strip()
    search_query = str(state.get("search_query", "")).strip()
    history = state.get("history", [])

    if not isinstance(history, list):
        history = [str(history)]

    history_str = "\n".join(map(str, history)) if history else "No previous conversation."

    # Fast path for clear greetings/small-talk openers
    q_lower = raw_question.lower()
    greeting_set = {"hi", "hello", "hey", "hi there", "hello there", "hey there"}
    if q_lower in greeting_set:
        return {
            "next_active_agent": "conversational_agent",
            "routing_reason": "greeting_fast_path",
        }

    structured_supervisor = llm.with_structured_output(SupervisorRoute)

    system_msg = (
        "You are a supervisor router for a multi-agent assistant. "
        "Choose 'document_agent' when the user needs grounded facts from indexed knowledge/documents, "
        "database checks, verification, or follow-up factual retrieval. "
        "Choose 'conversational_agent' only for pure greetings, casual small talk, or non-factual chat. "
        "If uncertain, choose 'document_agent'."
    )

    try:
        result = cast(
            SupervisorRoute,
            structured_supervisor.invoke(
                [
                    ("system", system_msg),
                    (
                        "human",
                        f"History:\n{history_str}\n\n"
                        f"Raw Question:\n{raw_question}\n\n"
                        f"Condensed Query (if any):\n{search_query}",
                    ),
                ]
            ),
        )

        target = result.next_active_agent
        if target not in ["document_agent", "conversational_agent"]:
            target = "document_agent"

        print(f"DEBUG: Supervisor chose -> {target}")
        return {
            "next_active_agent": target,
            "routing_reason": result.reason,
        }

    except Exception as e:
        print(f"⚠️ Supervisor routing failed: {e}")
        return {
            "next_active_agent": "document_agent",
            "routing_reason": "fallback_on_error",
        }

# 8. returns safe value for graph conditional edges.
def pick_active_agent(state: GraphState):
    target = state.get("next_active_agent", "document_agent")
    if target not in ["document_agent", "conversational_agent"]:
        return "document_agent"
    return target

# 9. handles non-RAG chat path and writes response/history
def conversational_agent(state: GraphState):
    print("--- NODE: CONVERSATIONAL AGENT ---")
    question = state.get("question", "")
    history = state.get("history", [])

    if not isinstance(history, list):
        history = [str(history)]

    history_str = "\n".join(map(str, history)) if history else "No previous conversation."

    system_msg = (
        "You are a helpful conversational assistant. "
        "Handle greetings, small talk, and memory-style follow-ups naturally. "
        "If document facts are unavailable, respond honestly."
    )

    response = llm.invoke([
        ("system", system_msg),
        ("human", f"History:\n{history_str}\n\nUser question:\n{question}")
    ])

    answer_text = str(response.content)

    return {
        "response": answer_text,
        "sources": [],
        "history": [f"User: {question}", f"AI: {answer_text}"]
    }
# 9. Condense Query
def condense_query(state: GraphState):
    print("--- NODE: CONDENSING QUERY ---")
    question = str(state.get("question", "")).strip()
    history = state.get("history", [])

    if not isinstance(history, list):
        history = [str(history)]

    history_str = "\n".join(map(str, history)) if history else "No previous conversation."

    structured_condense = llm.with_structured_output(CondensedQuery)

    system_msg = (
        "Rewrite ONLY the latest user question into a standalone question using history. "
        "Do NOT answer. Do NOT output facts, addresses, names, or explanations. "
        "Keep the same intent. If already standalone, return it unchanged."
    )

    try:
        result = cast(
            CondensedQuery,
            structured_condense.invoke([
                ("system", system_msg),
                ("human", f"History:\n{history_str}\n\nLatest user question:\n{question}")
            ])
        )

        standalone = str(result.standalone_query).strip()
        if not standalone:
            standalone = question

        # Guardrail: avoid fact-like outputs replacing the query
        bad_fact_like = ("\n" not in standalone and "?" not in standalone and len(standalone.split()) <= 8)
        if bad_fact_like and len(question.split()) >= 3:
            standalone = question

        print(f"DEBUG: Condensed query -> {standalone}")
        return {"search_query": standalone}

    except Exception as e:
        print(f"⚠️ Condense failed: {e}")
        return {"search_query": question}    
#10 
def no_context_fallback(state: GraphState):
    print("--- NODE: NO CONTEXT FALLBACK ---")
    question = state.get("question", "")
    return {
        "response": (
            "I could not find enough grounded information in the indexed documents "
            f"to answer: '{question}'. Please rephrase your question or ingest the correct document."
        ),
        "sources": state.get("sources", []),
        "history": [
            f"User: {question}",
            "AI: I could not find enough grounded information in the indexed documents."
        ],
        "no_context_fallback": True
    }
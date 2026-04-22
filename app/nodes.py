from typing import List, cast, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.llm import llm
from app.graph import GraphState
from app.engine import get_context_from_qdrant
from app.schemas import RouteQuery, GradeSchema, SupervisorRoute
from app.evaluator import check_faithfulness

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
    
    # 🚨 Put this line back in!
    print(f"DEBUG: Current iteration: {count}, Relevance: {relevance}")
    
    if relevance == "yes" or count >= 1:
        print("--- DECISION: GENERATE (Limit reached or relevant) ---")
        return "generate"
    else:
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
    question = state.get("question", "")
    history = state.get("history", [])

    if not isinstance(history, list):
        history = [str(history)]

    history_str = "\n".join(map(str, history)) if history else "No previous conversation."

    structured_supervisor = llm.with_structured_output(SupervisorRoute)

    system_msg = (
        "You are a supervisor router. "
        "Choose 'document_agent' for documen/factual/context-dependent queries. "
        "Choose 'conversational_agent' for greetings, casual chat, and lightweight conversation. "
        "If uncertain, choose 'document_agent'."
    )

    try:
        result = cast(
            SupervisorRoute,
            structured_supervisor.invoke([
                ("system", system_msg),
                ("human", f"History:\n{history_str}\n\nQuestion:\n{question}")
            ])
        )

        target = result.next_active_agent
        if target not in ["document_agent", "conversational_agent"]:
            target = "document_agent"

        print(f"DEBUG: Supervisor chose -> {target}")
        return {
            "next_active_agent": target,
            "routing_reason": result.reason
        }

    except Exception as e:
        print(f"⚠️ Supervisor routing failed: {e}")
        return {
            "next_active_agent": "document_agent",
            "routing_reason": "fallback_on_error"
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
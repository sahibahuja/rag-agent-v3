from langgraph.graph import StateGraph, END
from app.schemas import GraphState
from app.nodes import (
    condense_query,
    no_context_fallback,
    supervisor_route,
    pick_active_agent,
    conversational_agent,
    retrieve_docs,
    grade_documents,
    generate_answer,
    decide_to_generate,
    rewrite_query,
    summarize_memory
)

builder = StateGraph(GraphState)

# Nodes
builder.add_node("condense", condense_query)
builder.add_node("supervisor", supervisor_route)
builder.add_node("conversational", conversational_agent)
builder.add_node("retrieve", retrieve_docs)
builder.add_node("grade", grade_documents)
builder.add_node("rewrite", rewrite_query)
builder.add_node("generate", generate_answer)
builder.add_node("no_context", no_context_fallback)
builder.add_node("summarize", summarize_memory)

# Entry: always start at condensequery
builder.set_entry_point("condense")
builder.add_edge("condense", "supervisor")

# Supervisor conditional route
builder.add_conditional_edges(
    "supervisor",
    pick_active_agent,
    {
        "document_agent": "retrieve",
        "conversational_agent": "conversational",
    },
)

# Document spoke flow
builder.add_edge("retrieve", "grade")
builder.add_conditional_edges(
    "grade",
    decide_to_generate,
    {
        "generate": "generate",
        "rewrite": "rewrite",
        "no_context": "no_context",
    },
)
builder.add_edge("rewrite", "retrieve")

# End nodes
builder.add_edge("generate", "summarize")
builder.add_edge("conversational", "summarize")
builder.add_edge("no_context", "summarize")
builder.add_edge("summarize", END)

agent_builder = builder
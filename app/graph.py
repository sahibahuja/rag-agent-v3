from langgraph.graph import StateGraph, END
from app.schemas import GraphState
from app.nodes import (
    supervisor_route,
    pick_active_agent,
    conversational_agent,
    retrieve_docs,
    grade_documents,
    generate_answer,
    decide_to_generate,
    rewrite_query,
)

builder = StateGraph(GraphState)

# Nodes
builder.add_node("supervisor", supervisor_route)
builder.add_node("conversational", conversational_agent)
builder.add_node("retrieve", retrieve_docs)
builder.add_node("grade", grade_documents)
builder.add_node("rewrite", rewrite_query)
builder.add_node("generate", generate_answer)

# Entry: always start at supervisor
builder.set_entry_point("supervisor")

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
    },
)
builder.add_edge("rewrite", "retrieve")

# End nodes
builder.add_edge("generate", END)
builder.add_edge("conversational", END)

agent_builder = builder
"""
LangGraph workflow for processing uploaded documents.

Supports three graph construction modes:
  - "cooccurrence" : InfraNodus-style co-occurrence (fast, no LLM cost)
  - "llm"          : LLM-based entity/relationship extraction (rich semantics)
  - "both"         : Runs BOTH modes in parallel and merges into one graph
"""

from langgraph.graph import StateGraph, END
from app.agents.state import ResearchState
from app.agents.doc_processor import doc_processor_node
from app.agents.extraction import extraction_node
from app.agents.cooccurrence_builder import cooccurrence_builder_node
from app.agents.graph_builder import graph_builder_node
from app.agents.vector_builder import vector_builder_node


def _route_after_doc_processing(state: ResearchState) -> str:
    """Route to the correct extraction path based on graph_mode."""
    mode = state.get("graph_mode", "cooccurrence")
    if mode == "llm":
        return "llm_only"
    elif mode == "both":
        return "both_modes"
    else:
        # Default to co-occurrence (InfraNodus-style)
        return "cooccurrence_only"


def build_document_workflow(graph_mode: str = "cooccurrence"):
    """
    Builds the state graph for document processing.
    
    Flows depending on mode:
      cooccurrence: START → doc_processor → cooccurrence_builder → [graph_builder, vector_builder] → END
      llm:          START → doc_processor → extraction → [graph_builder, vector_builder] → END
      both:         START → doc_processor → [extraction, cooccurrence_builder] → graph_builder → vector_builder → END
    """
    workflow = StateGraph(ResearchState)

    # ── Common nodes ──────────────────────────────────────────────
    workflow.add_node("doc_processor", doc_processor_node)
    workflow.add_node("graph_builder", graph_builder_node)
    workflow.add_node("vector_builder", vector_builder_node)

    # ── Mode-specific nodes ───────────────────────────────────────
    workflow.add_node("extraction", extraction_node)
    workflow.add_node("cooccurrence_builder", cooccurrence_builder_node)

    # ── Entry point ───────────────────────────────────────────────
    workflow.set_entry_point("doc_processor")

    if graph_mode == "llm":
        # LLM extraction → parallel store
        workflow.add_edge("doc_processor", "extraction")
        workflow.add_edge("extraction", "graph_builder")
        workflow.add_edge("extraction", "vector_builder")
        workflow.add_edge("graph_builder", END)
        workflow.add_edge("vector_builder", END)

    elif graph_mode == "both":
        # Parallel: LLM extraction + co-occurrence → merge into graph_builder
        workflow.add_edge("doc_processor", "extraction")
        workflow.add_edge("doc_processor", "cooccurrence_builder")
        workflow.add_edge("extraction", "graph_builder")
        workflow.add_edge("cooccurrence_builder", "graph_builder")
        workflow.add_edge("graph_builder", "vector_builder")
        workflow.add_edge("vector_builder", END)

    else:
        # Default: co-occurrence only (fast, free)
        workflow.add_edge("doc_processor", "cooccurrence_builder")
        workflow.add_edge("cooccurrence_builder", "graph_builder")
        workflow.add_edge("cooccurrence_builder", "vector_builder")
        workflow.add_edge("graph_builder", END)
        workflow.add_edge("vector_builder", END)

    # Compile the graph
    return workflow.compile()

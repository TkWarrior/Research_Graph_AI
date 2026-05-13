"""
LangGraph workflow for processing uploaded documents.
"""

from langgraph.graph import StateGraph, END
from app.agents.state import ResearchState
from app.agents.doc_processor import doc_processor_node
from app.agents.extraction import extraction_node
from app.agents.graph_builder import graph_builder_node
from app.agents.vector_builder import vector_builder_node


def build_document_workflow():
    """
    Builds the state graph for document processing.
    
    Flow:
    START -> doc_processor -> extraction -> [graph_builder, vector_builder] -> END
    """
    workflow = StateGraph(ResearchState)

    # Add nodes
    workflow.add_node("doc_processor", doc_processor_node)
    workflow.add_node("extraction", extraction_node)
    workflow.add_node("graph_builder", graph_builder_node)
    workflow.add_node("vector_builder", vector_builder_node)

    # Define edges
    workflow.set_entry_point("doc_processor")
    
    workflow.add_edge("doc_processor", "extraction")
    
    # We can parallelize the storage steps
    workflow.add_edge("extraction", "graph_builder")
    workflow.add_edge("extraction", "vector_builder")
    
    workflow.add_edge("graph_builder", END)
    workflow.add_edge("vector_builder", END)

    # Compile the graph
    return workflow.compile()

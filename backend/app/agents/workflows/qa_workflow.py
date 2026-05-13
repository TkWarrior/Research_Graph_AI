"""
LangGraph workflow for Hybrid RAG Question Answering.
"""

from langgraph.graph import StateGraph, END
from app.agents.state import ResearchState
from app.agents.vector_retriever import vector_retriever_node
from app.agents.graph_retriever import graph_retriever_node
from app.agents.hybrid_rag import hybrid_rag_node


def build_qa_workflow():
    """
    Builds the state graph for question answering.
    
    Flow:
    START -> [vector_retriever, graph_retriever] -> hybrid_rag -> END
    """
    workflow = StateGraph(ResearchState)

    # Add nodes
    workflow.add_node("vector_retriever", vector_retriever_node)
    workflow.add_node("graph_retriever", graph_retriever_node)
    workflow.add_node("hybrid_rag", hybrid_rag_node)

    # We use a dummy starting node to fork the execution easily
    def start_node(state: ResearchState) -> dict:
        return {"current_step": "qa_started"}
        
    workflow.add_node("start", start_node)

    # Define edges
    workflow.set_entry_point("start")
    
    # Fork to parallel retrieval
    workflow.add_edge("start", "vector_retriever")
    workflow.add_edge("start", "graph_retriever")
    
    # Join into hybrid rag
    workflow.add_edge("vector_retriever", "hybrid_rag")
    workflow.add_edge("graph_retriever", "hybrid_rag")
    
    workflow.add_edge("hybrid_rag", END)

    # Compile the graph
    return workflow.compile()

"""
Agent for building a co-occurrence graph from document chunks 

This replaces the LLM-based extraction as the *primary* graph construction
method when graph_mode is "cooccurrence" or "both".
"""

from app.agents.state import ResearchState
from app.services.text_network_service import TextNetworkService


def cooccurrence_builder_node(state: ResearchState) -> dict:
    """
    Builds a co-occurrence text network from the document's text chunks.
    Uses spaCy NLP to tokenize, lemmatize, and connect co-occurring terms.
    """
    chunk_texts = state.get("chunk_texts", [])

    if not chunk_texts:
        return {"errors": ["No text chunks available for co-occurrence analysis."]}

    try:
        service = TextNetworkService(window_size=5, min_weight=2)
        result = service.build_graph_from_chunks(chunk_texts)

        return {
            "cooccurrence_nodes": result["nodes"],
            "cooccurrence_edges": result["edges"],
            "current_step": "cooccurrence_building_complete",
        }
    except Exception as e:
        return {"errors": [f"Co-occurrence graph building failed: {str(e)}"]}

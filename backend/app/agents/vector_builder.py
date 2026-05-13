"""
Agent for embedding document chunks and storing them in ChromaDB.
"""

from app.agents.state import ResearchState
from app.services.embedding_service import EmbeddingService

def vector_builder_node(state: ResearchState) -> dict:
    """Embeds and stores document chunks in ChromaDB."""
    chunks = state.get("chunks", [])
    document_id = state.get("document_id")

    if not document_id:
        return {"errors": ["Missing document_id in vector_builder_node."]}

    if not chunks:
        return {"current_step": "vector_building_skipped"}

    embedding_service = EmbeddingService()
    
    try:
        count = embedding_service.store_chunks(document_id, chunks)
        return {
            "current_step": f"vector_building_complete_{count}_chunks"
        }
    except Exception as e:
        return {"errors": [f"Vector building failed: {str(e)}"]}

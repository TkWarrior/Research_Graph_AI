"""
Agent for retrieving context from ChromaDB.
"""

from app.agents.state import ResearchState
from app.services.embedding_service import EmbeddingService


def vector_retriever_node(state: ResearchState) -> dict:
    """Retrieves document chunks from ChromaDB based on the user's query."""
    query = state.get("query")
    document_id = state.get("document_id")

    if not query:
        return {"errors": ["No query provided for vector retrieval."]}

    embedding_service = EmbeddingService()
    
    try:
        # Retrieve top 5 similar chunks
        results = embedding_service.search_similar(query, top_k=5, document_id=document_id)
        
        return {
            "vector_context": results,
            "current_step": "vector_retrieval_complete"
        }
    except Exception as e:
        return {"errors": [f"Vector retrieval failed: {str(e)}"]}

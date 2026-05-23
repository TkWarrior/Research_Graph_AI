"""
Agent for retrieving context from ChromaDB.

Filters by workspace_id (primary) so the query retrieves context from
ALL documents in the workspace, not just a single file.
"""

from app.agents.state import ResearchState
from app.services.embedding_service import EmbeddingService


def vector_retriever_node(state: ResearchState) -> dict:
    """Retrieves document chunks from ChromaDB scoped to the current workspace."""
    query = state.get("query")
    workspace_id = state.get("workspace_id")   # primary scope — all docs in workspace
    document_id = state.get("document_id")     # optional secondary — single-file queries

    if not query:
        return {"errors": ["No query provided for vector retrieval."]}

    if not workspace_id:
        return {"errors": ["No workspace_id in state — cannot scope vector retrieval."]}

    embedding_service = EmbeddingService()

    try:
        results = embedding_service.search_similar(
            query=query,
            top_k=5,
            workspace_id=workspace_id,  # scopes retrieval to this workspace
            document_id=document_id,    # None in most Q&A flows; set for doc-specific queries
        )
        return {
            "vector_context": results,
            "current_step": "vector_retrieval_complete",
        }
    except Exception as e:
        return {"errors": [f"Vector retrieval failed: {str(e)}"]}

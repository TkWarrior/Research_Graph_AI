"""
Agent for retrieving information for specific subtopics.
"""

from app.agents.state import ResearchState
from app.services.embedding_service import EmbeddingService


def researcher_node(state: ResearchState) -> dict:
    """Retrieves document context for each subtopic."""
    subtopics = state.get("subtopics", [])
    document_id = state.get("document_id")

    if not subtopics:
        return {"current_step": "research_skipped"}

    embedding_service = EmbeddingService()
    all_results = []
    
    try:
        # We perform a vector search for each subtopic to gather a broad set of context
        for topic in subtopics:
            results = embedding_service.search_similar(topic, top_k=3, document_id=document_id)
            all_results.extend(results)
            
        # Deduplicate chunks based on their content
        unique_chunks = {}
        for res in all_results:
            content = res["content"]
            if content not in unique_chunks:
                unique_chunks[content] = res
                
        # To avoid making chunk_texts too large, we just pass the strings forward
        # for extraction and report generation
        chunk_texts = [res["content"] for res in unique_chunks.values()]
        
        return {
            "chunk_texts": chunk_texts,
            "current_step": "research_complete"
        }
    except Exception as e:
        return {"errors": [f"Research failed: {str(e)}"]}

"""
Agent for extracting entities and relationships using the LLM.
"""

from app.agents.state import ResearchState
from app.services.extraction_service import ExtractionService


async def extraction_node(state: ResearchState) -> dict:
    """Extracts entities and relationships from document chunks concurrently."""
    chunk_texts = state.get("chunk_texts", [])
    
    if not chunk_texts:
        return {"errors": ["No text chunks available for extraction."]}

    service = ExtractionService()
    
    try:
        # Extract concurrently (max 5 chunks at a time)
        result = await service.extract_from_chunks(chunk_texts, max_concurrency=5)
        
        return {
            "entities": result.entities,
            "relationships": result.relationships,
            "current_step": "extraction_complete"
        }
    except Exception as e:
        return {"errors": [f"Entity/Relationship extraction failed: {str(e)}"]}

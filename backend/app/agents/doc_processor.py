"""
Agent for processing documents and extracting text chunks.
"""

from app.agents.state import ResearchState
from app.services.document_processor import DocumentProcessor


def doc_processor_node(state: ResearchState) -> dict:
    """Parses a document file and extracts text chunks."""
    file_path = state.get("file_path")
    document_id = state.get("document_id")
    file_type = state.get("file_type")

    if not file_path or not document_id or not file_type:
        return {"errors": ["Missing required document metadata for processing."]}

    processor = DocumentProcessor()
    
    try:
        chunks = processor.process_document(file_path, document_id, file_type)
        chunk_texts = [c.content for c in chunks]
        
        return {
            "chunks": chunks,
            "chunk_texts": chunk_texts,
            "current_step": "doc_processing_complete"
        }
    except Exception as e:
        return {"errors": [f"Document processing failed: {str(e)}"]}

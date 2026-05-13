"""
Service for extracting text from PDF and DOCX files, and chunking it for vector storage.
"""

import os
from typing import List, Dict, Any
import pymupdf4llm
from docx import Document as DocxDocument
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import get_settings

settings = get_settings()


class DocumentChunk:
    """Represents a chunk of text from a document with metadata."""
    def __init__(self, content: str, metadata: Dict[str, Any]):
        self.content = content
        self.metadata = metadata

    def __repr__(self):
        return f"<DocumentChunk page={self.metadata.get('page', 'unknown')} len={len(self.content)}>"


class DocumentProcessor:
    """Handles text extraction and chunking for uploaded documents."""

    def __init__(self):
        # Target ~800 tokens per chunk. Approximating 1 token = 4 chars -> 3200 chars.
        # We'll use 3000 chars with 400 overlap.
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=3000,
            chunk_overlap=400,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )

    def process_document(self, file_path: str, document_id: str, file_type: str) -> List[DocumentChunk]:
        """Extract text and split it into chunks with metadata."""
        if file_type.lower() == "pdf":
            return self._process_pdf(file_path, document_id)
        elif file_type.lower() == "docx":
            return self._process_docx(file_path, document_id)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

    def _process_pdf(self, file_path: str, document_id: str) -> List[DocumentChunk]:
        """Extract Markdown from PDF using pymupdf4llm, preserving page metadata."""
        # page_chunks=True returns a list of dictionaries, one per page
        # Each dictionary has keys like 'text', 'metadata', 'page_number'
        md_pages = pymupdf4llm.to_markdown(file_path, page_chunks=True)
        
        final_chunks = []
        
        for page_data in md_pages:
            page_text = page_data.get("text", "")
            page_num = page_data.get("metadata", {}).get("page", 0) + 1 # 1-indexed
            
            if not page_text.strip():
                continue

            # Further chunk the page text if it exceeds chunk_size
            sub_chunks = self.text_splitter.split_text(page_text)
            
            for i, chunk_text in enumerate(sub_chunks):
                metadata = {
                    "document_id": str(document_id),
                    "page": page_num,
                    "chunk_index_in_page": i
                }
                final_chunks.append(DocumentChunk(content=chunk_text, metadata=metadata))
                
        return final_chunks

    def _process_docx(self, file_path: str, document_id: str) -> List[DocumentChunk]:
        """Extract text from DOCX and chunk it. (DOCX doesn't have strict pages)."""
        doc = DocxDocument(file_path)
        full_text = "\n\n".join([para.text for para in doc.paragraphs if para.text.strip()])
        
        final_chunks = []
        sub_chunks = self.text_splitter.split_text(full_text)
        
        for i, chunk_text in enumerate(sub_chunks):
            metadata = {
                "document_id": str(document_id),
                "page": 1, # Default to 1 for DOCX since it lacks pagination
                "chunk_index": i
            }
            final_chunks.append(DocumentChunk(content=chunk_text, metadata=metadata))
            
        return final_chunks

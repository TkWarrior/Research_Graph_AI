"""
Service for managing vector embeddings and retrieving document chunks using ChromaDB.
"""

from typing import List, Dict, Any
import chromadb
from langchain_chroma import Chroma
from langchain_nomic.embeddings import NomicEmbeddings
from langchain_core.documents import Document

from app.config import get_settings
from app.services.document_processor import DocumentChunk

settings = get_settings()


class EmbeddingService:
    """Manages embedding generation and ChromaDB interactions."""

    def __init__(self):
        # Initialize Nomic Embeddings
        self.embeddings = NomicEmbeddings(
            model=settings.EMBEDDING_MODEL,
            nomic_api_key=settings.NOMIC_API_KEY
        )

        # Initialize persistent ChromaDB client
        self.chroma_client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
        
        # Create or get the collection
        self.collection = self.chroma_client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"} # Cosine similarity
        )

        # Initialize LangChain wrapper for convenience
        self.vector_store = Chroma(
            client=self.chroma_client,
            collection_name=settings.CHROMA_COLLECTION_NAME,
            embedding_function=self.embeddings,
        )

    def store_chunks(self, document_id: str, chunks: List[DocumentChunk]) -> int:
        """Embed and store a list of document chunks into ChromaDB."""
        if not chunks:
            return 0

        documents = []
        for chunk in chunks:
            # LangChain Chroma expects 'Document' objects
            doc = Document(
                page_content=chunk.content,
                metadata=chunk.metadata
            )
            documents.append(doc)

        # Generate unique IDs for each chunk based on document ID and chunk index
        ids = [
            f"{document_id}_p{c.metadata.get('page', 0)}_{c.metadata.get('chunk_index', c.metadata.get('chunk_index_in_page', 0))}"
            for c in chunks
        ]

        self.vector_store.add_documents(documents=documents, ids=ids)
        return len(chunks)

    def search_similar(self, query: str, top_k: int = 5, document_id: str = None) -> List[Dict[str, Any]]:
        """Retrieve the most similar document chunks to a query."""
        
        # Optional metadata filter
        filter_dict = None
        if document_id:
            filter_dict = {"document_id": str(document_id)}

        results = self.vector_store.similarity_search_with_relevance_scores(
            query,
            k=top_k,
            filter=filter_dict
        )

        # Format output
        formatted_results = []
        for doc, score in results:
            formatted_results.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "relevance_score": float(score)
            })

        return formatted_results

    def delete_document(self, document_id: str) -> None:
        """Delete all chunks associated with a specific document ID."""
        # We need to query for the IDs first, then delete them
        results = self.collection.get(
            where={"document_id": str(document_id)},
            include=[]
        )
        
        ids_to_delete = results.get("ids", [])
        if ids_to_delete:
            self.collection.delete(ids=ids_to_delete)

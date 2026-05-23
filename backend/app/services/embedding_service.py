"""
Service for managing vector embeddings and retrieving document chunks using ChromaDB.

Every stored vector carries two metadata fields for scoping:
  - workspace_id : top-level isolation — retrieval is always filtered by this
  - document_id  : per-file traceability within the workspace
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

    def store_chunks(
        self,
        document_id: str,
        chunks: List[DocumentChunk],
        workspace_id: str = None,
    ) -> int:
        """
        Embed and store a list of document chunks into ChromaDB.

        Every chunk receives both workspace_id and document_id in its metadata
        so retrieval can be scoped at the workspace level while still being
        traceable back to the originating document.
        """
        if not chunks:
            return 0

        documents = []
        for chunk in chunks:
            # Inject workspace_id and document_id into each chunk's metadata
            # before storing so we can filter on them at query time.
            enriched_metadata = {
                **chunk.metadata,
                "document_id": str(document_id),
            }
            if workspace_id:
                enriched_metadata["workspace_id"] = str(workspace_id)

            doc = Document(
                page_content=chunk.content,
                metadata=enriched_metadata,
            )
            documents.append(doc)

        # Generate unique IDs for each chunk based on document ID and chunk index
        ids = [
            f"{document_id}_p{c.metadata.get('page', 0)}_{c.metadata.get('chunk_index', c.metadata.get('chunk_index_in_page', 0))}"
            for c in chunks
        ]

        self.vector_store.add_documents(documents=documents, ids=ids)
        return len(chunks)

    def search_similar(
        self,
        query: str,
        top_k: int = 5,
        workspace_id: str = None,
        document_id: str = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve the most similar document chunks to a query.

        Filtering priority:
          1. workspace_id (primary)  — always applied when provided
          2. document_id  (secondary) — narrows to a single file within the workspace
        """
        filter_dict = None

        if workspace_id and document_id:
            # Narrow to a specific file inside the workspace
            filter_dict = {
                "$and": [
                    {"workspace_id": {"$eq": str(workspace_id)}},
                    {"document_id": {"$eq": str(document_id)}},
                ]
            }
        elif workspace_id:
            # Retrieve across ALL documents in the workspace
            filter_dict = {"workspace_id": {"$eq": str(workspace_id)}}
        elif document_id:
            # Fallback: filter by document only (legacy / direct doc queries)
            filter_dict = {"document_id": {"$eq": str(document_id)}}

        results = self.vector_store.similarity_search_with_relevance_scores(
            query,
            k=top_k,
            filter=filter_dict,
        )

        formatted_results = []
        for doc, score in results:
            formatted_results.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "relevance_score": float(score),
            })

        return formatted_results

    def delete_document(self, document_id: str) -> None:
        """Delete all chunks associated with a specific document ID."""
        results = self.collection.get(
            where={"document_id": {"$eq": str(document_id)}},
            include=[]
        )
        ids_to_delete = results.get("ids", [])
        if ids_to_delete:
            self.collection.delete(ids=ids_to_delete)

    def delete_workspace(self, workspace_id: str) -> int:
        """
        Delete ALL chunks belonging to a workspace.
        Called when a workspace is deleted entirely.
        Returns the number of vectors removed.
        """
        results = self.collection.get(
            where={"workspace_id": {"$eq": str(workspace_id)}},
            include=[]
        )
        ids_to_delete = results.get("ids", [])
        if ids_to_delete:
            self.collection.delete(ids=ids_to_delete)
        return len(ids_to_delete)

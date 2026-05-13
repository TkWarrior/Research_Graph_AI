"""
Pydantic schemas for API request/response validation.
"""

from datetime import datetime
from uuid import UUID
from typing import Optional

from pydantic import BaseModel, Field


# ══════════════════════════════════════════════════════════════════════
# Document Schemas
# ══════════════════════════════════════════════════════════════════════


class DocumentOut(BaseModel):
    """Response schema for a document."""

    id: UUID
    filename: str
    original_filename: str
    file_type: str
    file_size: int
    status: str
    chunk_count: int
    entity_count: int
    relationship_count: int
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentUploadResponse(BaseModel):
    """Response after a successful file upload."""

    message: str
    document: DocumentOut


class DocumentListResponse(BaseModel):
    """Response for listing all documents."""

    documents: list[DocumentOut]
    total: int


# ══════════════════════════════════════════════════════════════════════
# Chat Schemas
# ══════════════════════════════════════════════════════════════════════


class ChatMessageOut(BaseModel):
    """Response schema for a single chat message."""

    id: UUID
    role: str
    content: str
    sources: Optional[list[dict]] = None
    graph_context: Optional[list[dict]] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatSessionOut(BaseModel):
    """Response schema for a chat session (summary)."""

    id: UUID
    title: Optional[str] = None
    document_id: Optional[UUID] = None
    message_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ChatSessionDetail(BaseModel):
    """Response schema for a chat session with all messages."""

    id: UUID
    title: Optional[str] = None
    document_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    messages: list[ChatMessageOut]

    model_config = {"from_attributes": True}


class ChatSessionListResponse(BaseModel):
    """Response for listing chat sessions."""

    sessions: list[ChatSessionOut]
    total: int


class ChatSessionCreateRequest(BaseModel):
    """Request to create a new chat session."""

    title: Optional[str] = None
    document_id: Optional[UUID] = None


class ChatSessionRenameRequest(BaseModel):
    """Request to rename a chat session."""

    title: str = Field(..., min_length=1, max_length=255)


# ══════════════════════════════════════════════════════════════════════
# Q&A / Ask Schemas
# ══════════════════════════════════════════════════════════════════════


class AskRequest(BaseModel):
    """Request to ask a question via Hybrid RAG."""

    question: str = Field(..., min_length=1)
    session_id: Optional[UUID] = None
    document_id: Optional[UUID] = None


class AskResponse(BaseModel):
    """Response from the Hybrid RAG Q&A."""

    answer: str
    session_id: UUID
    sources: list[dict] = []
    graph_context: list[dict] = []


# ══════════════════════════════════════════════════════════════════════
# Graph Snapshot Schemas
# ══════════════════════════════════════════════════════════════════════


class GraphSnapshotOut(BaseModel):
    """Response schema for a graph snapshot."""

    id: UUID
    document_id: UUID
    version: int
    node_count: int
    edge_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class GraphSnapshotDetail(BaseModel):
    """Response schema for a graph snapshot with full data."""

    id: UUID
    document_id: UUID
    version: int
    nodes: list[dict]
    edges: list[dict]
    node_count: int
    edge_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ══════════════════════════════════════════════════════════════════════
# Query / Research Schemas
# ══════════════════════════════════════════════════════════════════════


class QueryRequest(BaseModel):
    """Request for a research query."""

    query: str = Field(..., min_length=1)


class QueryResponse(BaseModel):
    """Response from the research workflow."""

    report: str
    entities_found: int = 0
    relationships_found: int = 0

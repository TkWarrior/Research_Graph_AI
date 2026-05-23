"""
Pydantic schemas for API request/response validation.
"""

from datetime import datetime
from uuid import UUID
from typing import List, Optional

from pydantic import BaseModel, Field


# ══════════════════════════════════════════════════════════════════════
# Workspace Schemas
# ══════════════════════════════════════════════════════════════════════


class WorkspaceCreate(BaseModel):
    """Request body to create a new workspace."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class WorkspaceUpdate(BaseModel):
    """Request body to rename or update a workspace."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None


class WorkspaceOut(BaseModel):
    """Response schema for a workspace (summary view)."""

    id: UUID
    name: str
    description: Optional[str] = None
    document_count: int = 0        # populated manually in the endpoint
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WorkspaceListResponse(BaseModel):
    """Response for listing all workspaces."""

    workspaces: List[WorkspaceOut]
    total: int


# ══════════════════════════════════════════════════════════════════════
# Document Schemas
# ══════════════════════════════════════════════════════════════════════


class DocumentOut(BaseModel):
    """Response schema for a document."""

    id: UUID
    workspace_id: UUID          # which workspace this document belongs to
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
    sources: Optional[List[dict]] = None
    graph_context: Optional[List[dict]] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatSessionOut(BaseModel):
    """Response schema for a chat session (summary)."""

    id: UUID
    title: Optional[str] = None
    workspace_id: UUID          # sessions are now workspace-scoped
    message_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ChatSessionDetail(BaseModel):
    """Response schema for a chat session with all messages."""

    id: UUID
    title: Optional[str] = None
    workspace_id: UUID
    created_at: datetime
    updated_at: datetime
    messages: List[ChatMessageOut]

    model_config = {"from_attributes": True}


class ChatSessionListResponse(BaseModel):
    """Response for listing chat sessions."""

    sessions: List[ChatSessionOut]
    total: int


class ChatSessionCreateRequest(BaseModel):
    """Request to create a new chat session."""

    title: Optional[str] = None
    workspace_id: UUID          # required — every session belongs to a workspace


class ChatSessionRenameRequest(BaseModel):
    """Request to rename a chat session."""

    title: str = Field(..., min_length=1, max_length=255)


# ══════════════════════════════════════════════════════════════════════
# Q&A / Ask Schemas
# ══════════════════════════════════════════════════════════════════════


class AskRequest(BaseModel):
    """Request to ask a question via Hybrid RAG."""

    question: str = Field(..., min_length=1)
    workspace_id: UUID          # required — scopes vector + graph retrieval
    session_id: Optional[UUID] = None   # if None, a new session is auto-created


class AskResponse(BaseModel):
    """Response from the Hybrid RAG Q&A."""

    answer: str
    workspace_id: UUID
    session_id: UUID
    sources: List[dict] = []
    graph_context: List[dict] = []


# ══════════════════════════════════════════════════════════════════════
# Graph Snapshot Schemas
# ══════════════════════════════════════════════════════════════════════


class GraphSnapshotOut(BaseModel):
    """Response schema for a graph snapshot (summary)."""

    id: UUID
    workspace_id: UUID          # primary scope — merged graph of the whole workspace
    document_id: Optional[UUID] = None  # nullable — which doc triggered this snapshot
    version: int
    node_count: int
    edge_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class GraphSnapshotDetail(BaseModel):
    """Response schema for a graph snapshot with full node/edge data."""

    id: UUID
    workspace_id: UUID
    document_id: Optional[UUID] = None
    version: int
    nodes: List[dict]
    edges: List[dict]
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
    workspace_id: UUID          # required — scopes document context for the research workflow


class QueryResponse(BaseModel):
    """Response from the research workflow."""

    report: str
    entities_found: int = 0
    relationships_found: int = 0

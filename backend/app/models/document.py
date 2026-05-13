"""
SQLAlchemy models for document metadata and graph snapshots.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Document(Base):
    """Represents an uploaded document (PDF/DOCX)."""

    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=False)
    file_type = Column(String(20), nullable=False)  # "pdf" or "docx"
    file_size = Column(Integer, nullable=False)  # bytes
    status = Column(
        String(30), nullable=False, default="uploaded"
    )  # uploaded | processing | completed | error
    chunk_count = Column(Integer, default=0)
    entity_count = Column(Integer, default=0)
    relationship_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    graph_snapshots = relationship(
        "GraphSnapshot", back_populates="document", cascade="all, delete-orphan"
    )
    chat_sessions = relationship(
        "ChatSession", back_populates="document", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Document {self.original_filename} ({self.status})>"


class GraphSnapshot(Base):
    """
    Serialized copy of a document's knowledge graph stored in PostgreSQL.
    Enables versioning, fast reload, and portability independent of Neo4j.
    """

    __tablename__ = "graph_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(
        UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False
    )
    version = Column(Integer, default=1)
    nodes = Column(JSON, nullable=False)  # [{name, type, description, ...}]
    edges = Column(JSON, nullable=False)  # [{source, target, type, description, ...}]
    node_count = Column(Integer, default=0)
    edge_count = Column(Integer, default=0)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    document = relationship("Document", back_populates="graph_snapshots")

    def __repr__(self):
        return f"<GraphSnapshot doc={self.document_id} v{self.version} ({self.node_count} nodes, {self.edge_count} edges)>"

"""
SQLAlchemy model for the Workspace entity.

A Workspace is the top-level container that groups together:
  - Uploaded documents (PDF/DOCX)
  - Chat sessions & message history
  - Knowledge graph snapshots (merged across all documents)

All other models (Document, ChatSession, GraphSnapshot) reference
a workspace_id instead of being globally scoped.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Workspace(Base):
    """
    A named research workspace that acts as an isolated container.
    Users switch between workspaces to keep projects separate.
    """

    __tablename__ = "workspaces"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # ── Owner FK (disabled until auth is enabled) ──────────────────────
    # owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # ── Relationships ──────────────────────────────────────────────────
    # owner = relationship("User", back_populates="workspaces")  # TODO: re-enable with auth
    documents = relationship(
        "Document",
        back_populates="workspace",
        cascade="all, delete-orphan",
        lazy="dynamic",   # use .count() without loading all rows
    )
    chat_sessions = relationship(
        "ChatSession",
        back_populates="workspace",
        cascade="all, delete-orphan",
        order_by="ChatSession.updated_at.desc()",
    )
    graph_snapshots = relationship(
        "GraphSnapshot",
        back_populates="workspace",
        cascade="all, delete-orphan",
        order_by="GraphSnapshot.version.desc()",
    )

    # ── Helpers ────────────────────────────────────────────────────────
    @property
    def document_count(self) -> int:
        """Return the number of documents in this workspace."""
        return self.documents.count()

    def __repr__(self):
        return f"<Workspace '{self.name}' ({self.id})>"

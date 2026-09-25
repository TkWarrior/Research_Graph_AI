"""
SQLAlchemy models for chat session and message persistence.

ChatSession is now scoped to a Workspace (not a single Document),
so a conversation can reason across all documents in that workspace.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class ChatSession(Base):
    """
    A chat session groups related Q&A messages together.
    Scoped to a Workspace so the conversation can span multiple documents.
    """

    __tablename__ = "chat_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(
        String(255), nullable=True
    )  # auto-generated from first message
    # ── Workspace FK ─────────────────────────────────────────────────
    workspace_id = Column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False
    )
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # ── Relationships ─────────────────────────────────────────────────
    messages = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at",
    )
    workspace = relationship("Workspace", back_populates="chat_sessions")

    def __repr__(self):
        return f"<ChatSession {self.id} ws='{self.workspace_id}' title='{self.title}'>"


class ChatMessage(Base):
    """
    A single message in a chat session (user question or assistant answer).
    Stores retrieval context (sources + graph) alongside the message content.
    """

    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True), ForeignKey("chat_sessions.id"), nullable=False
    )
    role = Column(String(20), nullable=False)  # "user" | "assistant"
    content = Column(Text, nullable=False)
    sources = Column(JSON, nullable=True)  # vector retrieval sources
    graph_context = Column(JSON, nullable=True)  # graph retrieval context
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    session = relationship("ChatSession", back_populates="messages")

    def __repr__(self):
        return f"<ChatMessage {self.role}: {self.content[:50]}...>"

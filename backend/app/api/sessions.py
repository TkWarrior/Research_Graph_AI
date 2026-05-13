"""
API endpoints for managing chat sessions.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.chat import ChatSession, ChatMessage
from app.models.schemas import (
    ChatSessionOut, ChatSessionDetail, ChatSessionListResponse, 
    ChatSessionCreateRequest, ChatSessionRenameRequest
)

router = APIRouter()


@router.get("/", response_model=ChatSessionListResponse)
def list_sessions(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """List all chat sessions, ordered by most recent."""
    sessions = db.query(ChatSession).order_by(ChatSession.updated_at.desc()).offset(skip).limit(limit).all()
    total = db.query(ChatSession).count()
    
    # Calculate message counts
    for session in sessions:
        session.message_count = len(session.messages)
        
    return ChatSessionListResponse(sessions=sessions, total=total)


@router.get("/{session_id}", response_model=ChatSessionDetail)
def get_session(session_id: str, db: Session = Depends(get_db)):
    """Get full details and all messages for a specific chat session."""
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/", response_model=ChatSessionOut)
def create_session(request: ChatSessionCreateRequest, db: Session = Depends(get_db)):
    """Manually create a new empty chat session."""
    session = ChatSession(
        title=request.title or "New Chat",
        document_id=request.document_id
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    session.message_count = 0
    return session


@router.patch("/{session_id}", response_model=ChatSessionOut)
def rename_session(session_id: str, request: ChatSessionRenameRequest, db: Session = Depends(get_db)):
    """Rename a chat session."""
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    session.title = request.title
    db.commit()
    db.refresh(session)
    session.message_count = len(session.messages)
    return session


@router.delete("/{session_id}")
def delete_session(session_id: str, db: Session = Depends(get_db)):
    """Delete a chat session and all its messages."""
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    db.delete(session)
    db.commit()
    return {"message": "Session deleted successfully"}

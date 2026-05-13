"""
API endpoints for Q&A via Hybrid RAG.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.schemas import AskRequest, AskResponse
from app.models.chat import ChatSession, ChatMessage
from app.agents.workflows.qa_workflow import build_qa_workflow
from app.agents.state import ResearchState

router = APIRouter()
qa_app = build_qa_workflow()


@router.post("/", response_model=AskResponse)
async def ask_question(request: AskRequest, db: Session = Depends(get_db)):
    """
    Ask a question and get an answer using Hybrid RAG (Vector + Graph retrieval).
    Automatically saves the conversation to a chat session.
    """
    try:
        # 1. Manage Chat Session
        session_id = request.session_id
        if session_id:
            chat_session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
            if not chat_session:
                raise HTTPException(status_code=404, detail="Session not found")
        else:
            # Create a new session
            chat_session = ChatSession(
                title=request.question[:50] + "..." if len(request.question) > 50 else request.question,
                document_id=request.document_id
            )
            db.add(chat_session)
            db.flush()
            session_id = chat_session.id

        # 2. Save user message
        user_msg = ChatMessage(
            session_id=session_id,
            role="user",
            content=request.question
        )
        db.add(user_msg)
        db.commit()

        # 3. Execute LangGraph QA Workflow
        initial_state = ResearchState(
            query=request.question,
            document_id=str(request.document_id) if request.document_id else None,
            errors=[]
        )
        
        final_state = await qa_app.ainvoke(initial_state)

        if final_state.get("errors"):
            raise Exception(" | ".join(final_state["errors"]))

        # Extract results
        answer = final_state.get("answer", "I could not find an answer to your question.")
        vector_ctx = final_state.get("vector_context", [])
        graph_ctx = final_state.get("graph_context", [])

        # 4. Save assistant response with context
        assistant_msg = ChatMessage(
            session_id=session_id,
            role="assistant",
            content=answer,
            sources=vector_ctx,
            graph_context=graph_ctx
        )
        db.add(assistant_msg)
        
        # Update session timestamp
        chat_session.updated_at = assistant_msg.created_at
        db.commit()

        return AskResponse(
            answer=answer,
            session_id=session_id,
            sources=vector_ctx,
            graph_context=graph_ctx
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

"""
API endpoints for handling document uploads.
"""

import os
import shutil
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models.document import Document
from app.models.workspace import Workspace
from app.models.schemas import DocumentUploadResponse
from app.utils.helpers import ensure_directory, get_file_extension

settings = get_settings()
router = APIRouter()

ALLOWED_EXTENSIONS = {"pdf", "docx"}


@router.get("/documents")
def list_documents(
    workspace_id: str = None,
    db: Session = Depends(get_db)
):
    """List uploaded documents. Filter by workspace_id when provided."""
    query = db.query(Document).order_by(Document.created_at.desc())
    if workspace_id:
        query = query.filter(Document.workspace_id == workspace_id)
    docs = query.all()
    return [
        {
            "id": str(doc.id),
            "workspace_id": str(doc.workspace_id),
            "original_filename": doc.original_filename,
            "file_type": doc.file_type,
            "status": doc.status,
            "chunk_count": doc.chunk_count,
            "entity_count": doc.entity_count,
            "created_at": doc.created_at.isoformat() if doc.created_at else None,
        }
        for doc in docs
    ]


@router.post("/", response_model=DocumentUploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    workspace_id: str = Form(..., description="ID of the workspace this document belongs to"),
    graph_mode: str = Form(default="cooccurrence"),
    db: Session = Depends(get_db)
):
    """
    Upload a document (PDF or DOCX) into a specific workspace.
    The file is saved locally and processing is queued as a background task.

    graph_mode options:
      - "cooccurrence" (default): InfraNodus-style co-occurrence graph (fast, no LLM)
      - "llm": LLM-based entity/relationship extraction (rich, slower)
      - "both": Run both modes in parallel
    """
    # 1. Validate the workspace exists
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail=f"Workspace '{workspace_id}' not found")

    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    ext = get_file_extension(file.filename)
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Allowed: {ALLOWED_EXTENSIONS}"
        )

    # 2. Prepare upload directory
    upload_dir = ensure_directory(settings.UPLOAD_DIR)

    # 3. Create database record (status = "uploaded"), stamped with workspace_id
    db_doc = Document(
        original_filename=file.filename,
        filename=f"temp_{file.filename}",
        file_type=ext,
        file_size=0,
        status="uploaded",
        workspace_id=workspace_id,         # ← workspace scope
    )
    db.add(db_doc)
    db.flush()  # get the UUID

    # 4. Rename file using UUID
    unique_filename = f"{db_doc.id}.{ext}"
    file_path = os.path.join(upload_dir, unique_filename)
    db_doc.filename = unique_filename

    # 5. Save file to disk
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        file_size = os.path.getsize(file_path)
        db_doc.file_size = file_size

        if file_size > (settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024):
            os.remove(file_path)
            raise HTTPException(
                status_code=400,
                detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB"
            )

        db.commit()
        db.refresh(db_doc)

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # 6. Trigger LangGraph document processing pipeline in the background
    background_tasks.add_task(
        process_document_pipeline,
        db_doc.id, file_path, ext, graph_mode, workspace_id   # ← workspace_id forwarded
    )

    return DocumentUploadResponse(
        message="Document uploaded successfully and queued for processing.",
        document=db_doc
    )

async def process_document_pipeline(
    document_id: str,
    file_path: str,
    file_type: str,
    graph_mode: str = "cooccurrence",
    workspace_id: str = None,       # forwarded from upload_document
):
    """Background task to run the full document ingestion LangGraph workflow."""
    from app.agents.workflows.document_workflow import build_document_workflow
    from app.agents.state import ResearchState
    from app.database import SessionLocal

    app = build_document_workflow(graph_mode=graph_mode)
    db = SessionLocal()

    initial_state = ResearchState(
        document_id=str(document_id),
        workspace_id=str(workspace_id) if workspace_id else None,  # ← flows to every node
        file_path=file_path,
        file_type=file_type,
        graph_mode=graph_mode,
        errors=[]
    )

    try:
        db_doc = db.query(Document).filter(Document.id == document_id).first()
        if db_doc:
            db_doc.status = "processing"
            db.commit()

        final_state = await app.ainvoke(initial_state)

        db_doc = db.query(Document).filter(Document.id == document_id).first()
        if db_doc:
            if final_state.get("errors"):
                db_doc.status = "failed"
                db_doc.error_message = " | ".join(final_state["errors"])
            else:
                db_doc.status = "completed"
                db_doc.entity_count = len(final_state.get("entities", []))
                db_doc.relationship_count = len(final_state.get("relationships", []))
                db_doc.chunk_count = len(final_state.get("chunks", []))
            db.commit()

    except Exception as e:
        db_doc = db.query(Document).filter(Document.id == document_id).first()
        if db_doc:
            db_doc.status = "failed"
            db_doc.error_message = str(e)
            db.commit()
    finally:
        db.close()

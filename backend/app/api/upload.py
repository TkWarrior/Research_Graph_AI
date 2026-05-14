"""
API endpoints for handling document uploads.
"""

import os
import shutil
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models.document import Document
from app.models.schemas import DocumentUploadResponse
from app.utils.helpers import ensure_directory, get_file_extension

settings = get_settings()
router = APIRouter()

ALLOWED_EXTENSIONS = {"pdf", "docx"}


@router.get("/documents")
def list_documents(db: Session = Depends(get_db)):
    """List all uploaded documents (for the document selector)."""
    docs = db.query(Document).order_by(Document.created_at.desc()).all()
    return [
        {
            "id": str(doc.id),
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
    graph_mode: str = "cooccurrence",
    db: Session = Depends(get_db)
):
    """
    Upload a document (PDF or DOCX) for processing.
    The file is saved locally, and a database record is created.
    Processing happens asynchronously.
    
    graph_mode options:
      - "cooccurrence" (default): InfraNodus-style co-occurrence graph (fast, no LLM)
      - "llm": LLM-based entity/relationship extraction (rich, slower)
      - "both": Run both modes in parallel
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    ext = get_file_extension(file.filename)
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Allowed: {ALLOWED_EXTENSIONS}"
        )

    # Prepare upload directory
    upload_dir = ensure_directory(settings.UPLOAD_DIR)

    # Create database record first (status = "uploaded")
    db_doc = Document(
        original_filename=file.filename,
        filename=f"temp_{file.filename}", # We will rename it after saving
        file_type=ext,
        file_size=0, # Will update after save
        status="uploaded"
    )
    db.add(db_doc)
    db.flush() # Get the UUID

    # Now we have the UUID, let's rename the file uniquely
    unique_filename = f"{db_doc.id}.{ext}"
    file_path = os.path.join(upload_dir, unique_filename)
    
    db_doc.filename = unique_filename

    # Save file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        file_size = os.path.getsize(file_path)
        db_doc.file_size = file_size
        
        # Enforce size limit
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

    # Trigger LangGraph document processing pipeline in the background
    background_tasks.add_task(
        process_document_pipeline, db_doc.id, file_path, ext, graph_mode
    )

    return DocumentUploadResponse(
        message="Document uploaded successfully and queued for processing.",
        document=db_doc
    )

async def process_document_pipeline(
    document_id: str, file_path: str, file_type: str, graph_mode: str = "cooccurrence"
):
    """Background task to run the full document ingestion LangGraph workflow."""
    from app.agents.workflows.document_workflow import build_document_workflow
    from app.agents.state import ResearchState
    from app.database import SessionLocal
    
    app = build_document_workflow(graph_mode=graph_mode)
    db = SessionLocal()
    
    initial_state = ResearchState(
        document_id=str(document_id),
        file_path=file_path,
        file_type=file_type,
        graph_mode=graph_mode,
        errors=[]
    )
    
    # Run the graph
    try:
        # Update status to processing
        db_doc = db.query(Document).filter(Document.id == document_id).first()
        if db_doc:
            db_doc.status = "processing"
            db.commit()

        final_state = await app.ainvoke(initial_state)
        
        # Check for errors
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

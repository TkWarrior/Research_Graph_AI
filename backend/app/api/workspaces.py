"""
API endpoints for managing Workspaces.

A Workspace is the top-level container that groups together documents,
chat sessions, knowledge graphs, and insights.

Endpoints:
  POST   /api/workspaces/           — Create a new workspace
  GET    /api/workspaces/           — List all workspaces
  GET    /api/workspaces/{id}       — Get workspace details + document list
  PATCH  /api/workspaces/{id}       — Rename / update a workspace
  DELETE /api/workspaces/{id}       — Delete workspace + cascade all data
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.workspace import Workspace
from app.models.document import Document
from app.models.schemas import (
    WorkspaceCreate,
    WorkspaceUpdate,
    WorkspaceOut,
    WorkspaceListResponse,
)

router = APIRouter()


# ══════════════════════════════════════════════════════════════════════
# Create
# ══════════════════════════════════════════════════════════════════════

@router.post("/", response_model=WorkspaceOut, status_code=201)
def create_workspace(request: WorkspaceCreate, db: Session = Depends(get_db)):
    """Create a new isolated workspace."""
    workspace = Workspace(
        name=request.name,
        description=request.description,
    )
    db.add(workspace)
    db.commit()
    db.refresh(workspace)
    workspace_out = WorkspaceOut.model_validate(workspace)
    workspace_out.document_count = 0
    return workspace_out


# ══════════════════════════════════════════════════════════════════════
# Read
# ══════════════════════════════════════════════════════════════════════

@router.get("/", response_model=WorkspaceListResponse)
def list_workspaces(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """List all workspaces ordered by most recently updated."""
    workspaces = (
        db.query(Workspace)
        .order_by(Workspace.updated_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    total = db.query(Workspace).count()

    result = []
    for ws in workspaces:
        ws_out = WorkspaceOut.model_validate(ws)
        ws_out.document_count = ws.document_count   # uses the @property
        result.append(ws_out)

    return WorkspaceListResponse(workspaces=result, total=total)


@router.get("/{workspace_id}", response_model=WorkspaceOut)
def get_workspace(workspace_id: str, db: Session = Depends(get_db)):
    """Get full details of a single workspace."""
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    ws_out = WorkspaceOut.model_validate(workspace)
    ws_out.document_count = workspace.document_count
    return ws_out


# ══════════════════════════════════════════════════════════════════════
# Update
# ══════════════════════════════════════════════════════════════════════

@router.patch("/{workspace_id}", response_model=WorkspaceOut)
def update_workspace(
    workspace_id: str,
    request: WorkspaceUpdate,
    db: Session = Depends(get_db)
):
    """Rename or update a workspace. Only provided fields are changed."""
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    if request.name is not None:
        workspace.name = request.name
    if request.description is not None:
        workspace.description = request.description

    db.commit()
    db.refresh(workspace)

    ws_out = WorkspaceOut.model_validate(workspace)
    ws_out.document_count = workspace.document_count
    return ws_out


# ══════════════════════════════════════════════════════════════════════
# Delete
# ══════════════════════════════════════════════════════════════════════

@router.delete("/{workspace_id}")
def delete_workspace(workspace_id: str, db: Session = Depends(get_db)):
    """
    Delete a workspace and cascade-delete ALL associated data:
    - PostgreSQL: Documents, ChatSessions, GraphSnapshots (via FK cascade)
    - Neo4j: All nodes and edges tagged with this workspace_id
    - ChromaDB: All vectors tagged with this workspace_id
    """
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # 1. Delete Neo4j graph data
    try:
        from app.services.graph_service import GraphService
        graph_service = GraphService()
        neo4j_result = graph_service.delete_workspace_graph(workspace_id)
        graph_service.close()
    except Exception as e:
        neo4j_result = {"error": str(e)}

    # 2. Delete ChromaDB vectors
    try:
        from app.services.embedding_service import EmbeddingService
        embedding_service = EmbeddingService()
        chroma_deleted = embedding_service.delete_workspace(workspace_id)
    except Exception as e:
        chroma_deleted = {"error": str(e)}

    # 3. Delete PostgreSQL records (cascade deletes documents, sessions, snapshots)
    db.delete(workspace)
    db.commit()

    return {
        "message": f"Workspace '{workspace_id}' deleted successfully",
        "neo4j_deleted_nodes": neo4j_result.get("deleted_nodes", 0),
        "chroma_deleted_vectors": chroma_deleted if isinstance(chroma_deleted, int) else 0,
    }

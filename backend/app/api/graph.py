"""
API endpoints for graph visualization and snapshots.
Supports document-scoped graph queries via optional document_id parameter.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.graph_service import GraphService
from app.models.document import GraphSnapshot
from app.models.schemas import GraphSnapshotOut, GraphSnapshotDetail

router = APIRouter()


@router.get("/", response_model=Dict[str, Any])
def get_full_graph(
    limit: int = 500,
    document_id: Optional[str] = Query(default=None, description="Filter graph by document ID")
):
    """Get the knowledge graph from Neo4j. Optionally scoped to a single document."""
    service = GraphService()
    try:
        return service.get_full_graph(limit=limit, document_id=document_id)
    finally:
        service.close()


@router.get("/subgraph/{entity_name}", response_model=Dict[str, Any])
def get_subgraph(
    entity_name: str,
    depth: int = 2,
    document_id: Optional[str] = Query(default=None)
):
    """Get the neighborhood graph around a specific entity from Neo4j."""
    service = GraphService()
    try:
        return service.query_subgraph(entity_name, depth=depth, document_id=document_id)
    finally:
        service.close()


@router.get("/stats", response_model=Dict[str, Any])
def get_graph_stats(document_id: Optional[str] = Query(default=None)):
    """Get statistics about the Neo4j knowledge graph."""
    service = GraphService()
    try:
        return service.get_graph_stats(document_id=document_id)
    finally:
        service.close()


@router.delete("/document/{document_id}")
def delete_document_graph(document_id: str):
    """Delete the entire graph for a specific document from Neo4j."""
    service = GraphService()
    try:
        result = service.delete_document_graph(document_id)
        return {"message": f"Deleted graph for document {document_id}", **result}
    finally:
        service.close()


# ══════════════════════════════════════════════════════════════════════
# Snapshots (PostgreSQL)
# ══════════════════════════════════════════════════════════════════════

@router.get("/snapshots/{document_id}", response_model=List[GraphSnapshotOut])
def list_snapshots(document_id: str, db: Session = Depends(get_db)):
    """List all graph snapshots for a specific document."""
    snapshots = db.query(GraphSnapshot).filter(GraphSnapshot.document_id == document_id).order_by(GraphSnapshot.version.desc()).all()
    return snapshots


@router.get("/snapshots/{document_id}/latest", response_model=GraphSnapshotDetail)
def get_latest_snapshot(document_id: str, db: Session = Depends(get_db)):
    """Get the latest graph snapshot data for a document (fast, no Neo4j required)."""
    snapshot = db.query(GraphSnapshot).filter(GraphSnapshot.document_id == document_id).order_by(GraphSnapshot.version.desc()).first()
    if not snapshot:
        raise HTTPException(status_code=404, detail="No graph snapshot found for this document")
    return snapshot


@router.get("/snapshots/{document_id}/{version}", response_model=GraphSnapshotDetail)
def get_snapshot_version(document_id: str, version: int, db: Session = Depends(get_db)):
    """Get a specific version of a graph snapshot."""
    snapshot = db.query(GraphSnapshot).filter(
        GraphSnapshot.document_id == document_id,
        GraphSnapshot.version == version
    ).first()
    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot version not found")
    return snapshot

"""
API endpoints for graph visualization and snapshots.
All endpoints are scoped to a workspace_id for isolation.
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
    workspace_id: str = Query(..., description="Workspace ID to scope the graph"),
    limit: int = 500,
):
    """Get the knowledge graph from Neo4j, scoped to a workspace."""
    service = GraphService()
    try:
        return service.get_full_graph(limit=limit, workspace_id=workspace_id)
    finally:
        service.close()


@router.get("/seed", response_model=Dict[str, Any])
def get_seed_graph(
    workspace_id: str = Query(..., description="Workspace ID to scope the graph"),
    limit: int = Query(5, description="Number of top hub nodes to return"),
):
    """
    Return the top-N hub nodes (by degree) plus edges among them.
    This is the lightweight initial graph shown before any user exploration.
    """
    service = GraphService()
    try:
        return service.get_seed_graph(limit=limit, workspace_id=workspace_id)
    finally:
        service.close()


@router.get("/neighbors/{node_name}", response_model=Dict[str, Any])
def get_node_neighbors(
    node_name: str,
    workspace_id: str = Query(..., description="Workspace ID to scope the graph"),
):
    """
    Return the direct (depth-1) neighbors of a node.
    Called when the user clicks a node to expand it incrementally.
    """
    service = GraphService()
    try:
        return service.get_node_neighbors(node_name, workspace_id=workspace_id)
    finally:
        service.close()


@router.get("/subgraph/{entity_name}", response_model=Dict[str, Any])
def get_subgraph(
    entity_name: str,
    workspace_id: str = Query(..., description="Workspace ID to scope the graph"),
    depth: int = 2,
):
    """Get the neighborhood graph around a specific entity, scoped to a workspace."""
    service = GraphService()
    try:
        return service.query_subgraph(entity_name, depth=depth, workspace_id=workspace_id)
    finally:
        service.close()


@router.get("/stats", response_model=Dict[str, Any])
def get_graph_stats(
    workspace_id: str = Query(..., description="Workspace ID to scope the graph")
):
    """Get statistics about the workspace knowledge graph."""
    service = GraphService()
    try:
        return service.get_graph_stats(workspace_id=workspace_id)
    finally:
        service.close()


@router.delete("/document/{document_id}")
def delete_document_graph(document_id: str):
    """Delete the Neo4j graph for a specific document."""
    service = GraphService()
    try:
        result = service.delete_document_graph(document_id)
        return {"message": f"Deleted graph for document {document_id}", **result}
    finally:
        service.close()


# ══════════════════════════════════════════════════════════════════════
# Snapshots (PostgreSQL)
# ══════════════════════════════════════════════════════════════════════

@router.get("/snapshots/{workspace_id}", response_model=List[GraphSnapshotOut])
def list_snapshots(workspace_id: str, db: Session = Depends(get_db)):
    """List all graph snapshots for a workspace, newest version first."""
    snapshots = (
        db.query(GraphSnapshot)
        .filter(GraphSnapshot.workspace_id == workspace_id)
        .order_by(GraphSnapshot.version.desc())
        .all()
    )
    return snapshots


@router.get("/snapshots/{workspace_id}/latest", response_model=GraphSnapshotDetail)
def get_latest_snapshot(workspace_id: str, db: Session = Depends(get_db)):
    """Get the latest graph snapshot for a workspace (fast, no Neo4j required)."""
    snapshot = (
        db.query(GraphSnapshot)
        .filter(GraphSnapshot.workspace_id == workspace_id)
        .order_by(GraphSnapshot.version.desc())
        .first()
    )
    if not snapshot:
        raise HTTPException(status_code=404, detail="No graph snapshot found for this workspace")
    return snapshot


@router.get("/snapshots/{workspace_id}/{version}", response_model=GraphSnapshotDetail)
def get_snapshot_version(workspace_id: str, version: int, db: Session = Depends(get_db)):
    """Get a specific version of a graph snapshot for a workspace."""
    snapshot = db.query(GraphSnapshot).filter(
        GraphSnapshot.workspace_id == workspace_id,
        GraphSnapshot.version == version
    ).first()
    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot version not found")
    return snapshot

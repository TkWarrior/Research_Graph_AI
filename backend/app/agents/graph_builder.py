"""
Agent for storing extracted entities and relationships into Neo4j and saving snapshots.
Supports both LLM-extracted and co-occurrence graph data.

All Neo4j writes are tagged with workspace_id (primary scope) and
document_id (per-file traceability), matching the same strategy as ChromaDB.
"""

from app.agents.state import ResearchState
from app.services.graph_service import GraphService
from app.database import SessionLocal
from app.models.document import GraphSnapshot


def graph_builder_node(state: ResearchState) -> dict:
    """
    Stores entities, relationships, AND/OR co-occurrence data into Neo4j.
    Creates a workspace-scoped snapshot in Postgres for versioning.
    """
    entities = state.get("entities", [])
    relationships = state.get("relationships", [])
    cooccurrence_nodes = state.get("cooccurrence_nodes", [])
    cooccurrence_edges = state.get("cooccurrence_edges", [])
    document_id = state.get("document_id")
    workspace_id = state.get("workspace_id")   # primary scope for all graph writes

    if not document_id:
        return {"errors": ["Missing document_id in graph_builder_node."]}

    if not workspace_id:
        return {"errors": ["Missing workspace_id in graph_builder_node."]}

    has_llm_data = bool(entities or relationships)
    has_cooccurrence_data = bool(cooccurrence_nodes or cooccurrence_edges)

    if not has_llm_data and not has_cooccurrence_data:
        return {"current_step": "graph_building_skipped"}

    graph_service = GraphService()
    db = SessionLocal()

    try:
        # 1. Write LLM-extracted data to Neo4j (tagged with both IDs)
        if has_llm_data:
            graph_service.create_entities(
                entities,
                document_id=document_id,
                workspace_id=workspace_id,
            )
            graph_service.create_relationships(
                relationships,
                document_id=document_id,
                workspace_id=workspace_id,
            )

        # 2. Write co-occurrence data to Neo4j (tagged with both IDs)
        if has_cooccurrence_data:
            graph_service.create_cooccurrence_nodes(
                cooccurrence_nodes,
                document_id=document_id,
                workspace_id=workspace_id,
            )
            graph_service.create_cooccurrence_edges(
                cooccurrence_edges,
                document_id=document_id,
                workspace_id=workspace_id,
            )

        # 3. Save workspace-scoped snapshot to PostgreSQL
        snapshot_nodes = []
        snapshot_edges = []

        if has_llm_data:
            snapshot_nodes.extend([e.model_dump() for e in entities])
            snapshot_edges.extend([r.model_dump() for r in relationships])

        if has_cooccurrence_data:
            snapshot_nodes.extend(cooccurrence_nodes)
            snapshot_edges.extend(cooccurrence_edges)

        snapshot = GraphSnapshot(
            workspace_id=workspace_id,   # primary FK — workspace-scoped snapshot
            document_id=document_id,     # secondary — traceability to source file
            nodes=snapshot_nodes,
            edges=snapshot_edges,
            node_count=len(snapshot_nodes),
            edge_count=len(snapshot_edges),
        )
        db.add(snapshot)
        db.commit()

        return {"current_step": "graph_building_complete"}
    except Exception as e:
        db.rollback()
        return {"errors": [f"Graph building failed: {str(e)}"]}
    finally:
        graph_service.close()
        db.close()

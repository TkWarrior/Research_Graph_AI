"""
Agent for storing extracted entities and relationships into Neo4j and saving snapshots.
"""

from app.agents.state import ResearchState
from app.services.graph_service import GraphService
from app.database import SessionLocal
from app.models.document import GraphSnapshot

def graph_builder_node(state: ResearchState) -> dict:
    """Stores entities and relationships into Neo4j and creates a snapshot in Postgres."""
    entities = state.get("entities", [])
    relationships = state.get("relationships", [])
    document_id = state.get("document_id")

    if not document_id:
        return {"errors": ["Missing document_id in graph_builder_node."]}

    if not entities and not relationships:
        return {"current_step": "graph_building_skipped"}

    graph_service = GraphService()
    db = SessionLocal()
    
    try:
        # 1. Write to Neo4j
        graph_service.create_entities(entities)
        graph_service.create_relationships(relationships)
        
        # 2. Save snapshot to PostgreSQL
        snapshot = GraphSnapshot(
            document_id=document_id,
            nodes=[e.model_dump() for e in entities],
            edges=[r.model_dump() for r in relationships],
            node_count=len(entities),
            edge_count=len(relationships)
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

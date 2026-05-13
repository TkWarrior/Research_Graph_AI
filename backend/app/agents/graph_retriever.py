"""
Agent for retrieving context from Neo4j Knowledge Graph.
"""

from app.agents.state import ResearchState
from app.services.graph_service import GraphService
from app.services.extraction_service import ExtractionService


async def graph_retriever_node(state: ResearchState) -> dict:
    """Retrieves graph neighborhood context based on entities in the query."""
    query = state.get("query")

    if not query:
        return {"errors": ["No query provided for graph retrieval."]}

    # 1. First, we need to quickly extract entities from the user's query
    # to know what nodes to look up in Neo4j.
    extraction_service = ExtractionService()
    extracted = await extraction_service.extract_from_text(query)
    
    query_entities = extracted.entities

    if not query_entities:
        # No entities found in query, return empty graph context
        return {
            "graph_context": [],
            "current_step": "graph_retrieval_empty"
        }

    graph_service = GraphService()
    graph_context = []
    
    try:
        # 2. For each extracted entity, get its 1-hop or 2-hop neighborhood
        for entity in query_entities:
            # First, try to find the entity in the graph
            matches = graph_service.search_entities(entity.name, limit=1)
            
            if matches:
                matched_name = matches[0]["name"]
                # Get the subgraph
                subgraph = graph_service.query_subgraph(matched_name, depth=1)
                
                # Append to context
                if subgraph["edges"]:
                    graph_context.append({
                        "entity": matched_name,
                        "subgraph": subgraph
                    })
                    
        return {
            "graph_context": graph_context,
            "current_step": "graph_retrieval_complete"
        }
    except Exception as e:
        return {"errors": [f"Graph retrieval failed: {str(e)}"]}
    finally:
        graph_service.close()

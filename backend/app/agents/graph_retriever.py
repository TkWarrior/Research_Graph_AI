"""
Agent for retrieving context from Neo4j Knowledge Graph.
Filters all queries by workspace_id so retrieval stays isolated per workspace.
"""

from app.agents.state import ResearchState
from app.services.graph_service import GraphService
from app.services.extraction_service import ExtractionService


async def graph_retriever_node(state: ResearchState) -> dict:
    """Retrieves graph neighborhood context scoped to the current workspace."""
    query = state.get("query")
    workspace_id = state.get("workspace_id")   # primary scope

    if not query:
        return {"errors": ["No query provided for graph retrieval."]}

    if not workspace_id:
        return {"errors": ["No workspace_id in state — cannot scope graph retrieval."]}

    # 1. Extract entities from the user's query to know what nodes to look up.
    extraction_service = ExtractionService()
    extracted = await extraction_service.extract_from_text(query)
    query_entities = extracted.entities

    if not query_entities:
        return {
            "graph_context": [],
            "current_step": "graph_retrieval_empty",
        }

    graph_service = GraphService()
    graph_context = []

    try:
        for entity in query_entities:
            # Search within this workspace only
            matches = graph_service.search_entities(
                entity.name,
                limit=1,
                workspace_id=workspace_id,
            )

            if matches:
                matched_name = matches[0]["name"]
                # Get the 1-hop subgraph, scoped to workspace
                subgraph = graph_service.query_subgraph(
                    matched_name,
                    depth=1,
                    workspace_id=workspace_id,
                )

                if subgraph["edges"]:
                    graph_context.append({
                        "entity": matched_name,
                        "subgraph": subgraph,
                    })

        return {
            "graph_context": graph_context,
            "current_step": "graph_retrieval_complete",
        }
    except Exception as e:
        return {"errors": [f"Graph retrieval failed: {str(e)}"]}
    finally:
        graph_service.close()

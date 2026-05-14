"""
Analytics API — InfraNodus-style graph analytics endpoints.

All endpoints accept an optional `document_id` query parameter
to scope the analysis to a single document's graph.

Provides:
  GET /api/analytics/full       — Complete network analysis
  GET /api/analytics/centrality — Top nodes by betweenness centrality
  GET /api/analytics/communities— Community/cluster detection
  GET /api/analytics/gaps       — Structural gaps between clusters
  GET /api/analytics/stats      — Network-level statistics
  GET /api/analytics/graph-with-analytics — Enriched graph for frontend
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from loguru import logger

from app.services.graph_service import GraphService
from app.services.network_analysis_service import NetworkAnalysisService

router = APIRouter()


def _get_graph_data(limit: int = 1000, document_id: str = None):
    """Fetch raw node/edge data from Neo4j, optionally scoped to a document."""
    graph_service = GraphService()
    try:
        data = graph_service.get_full_graph(limit=limit, document_id=document_id)
        return data
    finally:
        graph_service.close()


@router.get("/full")
async def full_analysis(
    limit: int = 1000,
    document_id: Optional[str] = Query(default=None, description="Scope analysis to a specific document"),
):
    """
    Run the complete InfraNodus-style analysis on the knowledge graph.
    Returns centrality, communities, structural gaps, pagerank, and stats.
    """
    try:
        data = _get_graph_data(limit, document_id=document_id)
        
        if not data["nodes"]:
            return {
                "centrality": [],
                "communities": {"clusters": [], "modularity": 0},
                "gaps": [],
                "pagerank": [],
                "stats": {"node_count": 0, "edge_count": 0},
            }
        
        analyzer = NetworkAnalysisService()
        result = analyzer.full_analysis(data["nodes"], data["edges"])
        return result
    except Exception as e:
        logger.error(f"Full analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/centrality")
async def get_centrality(
    top_n: int = 20,
    limit: int = 1000,
    document_id: Optional[str] = Query(default=None),
):
    """Get the top-N nodes ranked by betweenness centrality."""
    try:
        data = _get_graph_data(limit, document_id=document_id)
        analyzer = NetworkAnalysisService()
        G = analyzer._build_nx_graph(data["nodes"], data["edges"])
        return {"centrality": analyzer.betweenness_centrality(G, top_n=top_n)}
    except Exception as e:
        logger.error(f"Centrality analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/communities")
async def get_communities(
    limit: int = 1000,
    document_id: Optional[str] = Query(default=None),
):
    """Detect topical clusters using Louvain community detection."""
    try:
        data = _get_graph_data(limit, document_id=document_id)
        analyzer = NetworkAnalysisService()
        G = analyzer._build_nx_graph(data["nodes"], data["edges"])
        communities = analyzer.detect_communities(G)
        
        response = {
            "clusters": communities["clusters"],
            "modularity": communities["modularity"],
            "total_clusters": len(communities["clusters"]),
        }
        return response
    except Exception as e:
        logger.error(f"Community detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/gaps")
async def get_structural_gaps(
    max_gaps: int = 5,
    limit: int = 1000,
    document_id: Optional[str] = Query(default=None),
):
    """Find structural gaps — weakly connected cluster pairs."""
    try:
        data = _get_graph_data(limit, document_id=document_id)
        analyzer = NetworkAnalysisService()
        G = analyzer._build_nx_graph(data["nodes"], data["edges"])
        communities = analyzer.detect_communities(G)
        gaps = analyzer.find_structural_gaps(G, communities, max_gaps=max_gaps)
        return {"gaps": gaps, "total_clusters": len(communities["clusters"])}
    except Exception as e:
        logger.error(f"Structural gap analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_network_stats(
    limit: int = 1000,
    document_id: Optional[str] = Query(default=None),
):
    """Get high-level network statistics."""
    try:
        data = _get_graph_data(limit, document_id=document_id)
        analyzer = NetworkAnalysisService()
        G = analyzer._build_nx_graph(data["nodes"], data["edges"])
        stats = analyzer.network_stats(G)
        return stats
    except Exception as e:
        logger.error(f"Network stats failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/graph-with-analytics")
async def get_graph_with_analytics(
    limit: int = 1000,
    document_id: Optional[str] = Query(default=None, description="Scope to a specific document"),
):
    """
    Returns the full graph data enriched with per-node analytics:
    each node gets a centrality score and community assignment.
    Designed for direct consumption by the frontend visualization.
    """
    try:
        data = _get_graph_data(limit, document_id=document_id)
        
        if not data["nodes"]:
            return {"nodes": [], "edges": [], "communities": {"clusters": []}}
        
        analyzer = NetworkAnalysisService()
        G = analyzer._build_nx_graph(data["nodes"], data["edges"])
        
        # Compute analytics
        bc = dict(
            (item["name"], item["centrality"])
            for item in analyzer.betweenness_centrality(G, top_n=9999)
        )
        communities = analyzer.detect_communities(G)
        node_communities = communities.get("node_communities", {})
        
        pr = dict(
            (item["name"], item["pagerank"])
            for item in analyzer.compute_pagerank(G, top_n=9999)
        )

        # Build cluster color lookup
        cluster_colors = {}
        for cluster in communities.get("clusters", []):
            cluster_colors[cluster["id"]] = cluster["color"]

        # Enrich nodes
        enriched_nodes = []
        for node in data["nodes"]:
            name = node.get("name") or node.get("id")
            community_id = node_communities.get(name, 0)
            enriched_nodes.append({
                **node,
                "centrality": bc.get(name, 0),
                "pagerank": pr.get(name, 0),
                "community": community_id,
                "community_color": cluster_colors.get(community_id, "#FFFFFF"),
            })

        return {
            "nodes": enriched_nodes,
            "edges": data["edges"],
            "communities": {
                "clusters": communities["clusters"],
                "modularity": communities["modularity"],
            },
        }
    except Exception as e:
        logger.error(f"Graph with analytics failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

"""
API endpoint for direct text input (InfraNodus-style).

Allows users to paste/type text directly and immediately generate
a co-occurrence knowledge graph — no file upload needed.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from loguru import logger

from app.services.text_network_service import TextNetworkService
from app.services.network_analysis_service import NetworkAnalysisService
from app.services.graph_service import GraphService

router = APIRouter()


class TextInputRequest(BaseModel):
    """Request body for direct text input."""
    text: str = Field(..., min_length=10, description="The text to analyze")
    window_size: int = Field(default=5, ge=2, le=10, description="Co-occurrence window size")
    min_weight: int = Field(default=2, ge=1, le=10, description="Minimum edge weight to keep")
    persist: bool = Field(default=False, description="Whether to save to Neo4j")


class TextInputResponse(BaseModel):
    """Response with the generated graph and analytics."""
    nodes: list
    edges: list
    analytics: Optional[dict] = None
    message: str


@router.post("/", response_model=TextInputResponse)
async def analyze_text(request: TextInputRequest):
    """
    Analyze raw text and return an InfraNodus-style co-occurrence graph
    with full network analytics (centrality, communities, gaps).
    
    Set `persist=true` to also save the graph to Neo4j.
    """
    try:
        # 1. Build co-occurrence graph
        service = TextNetworkService(
            window_size=request.window_size,
            min_weight=request.min_weight,
        )
        graph_data = service.build_graph_from_text(request.text)

        if not graph_data["nodes"]:
            return TextInputResponse(
                nodes=[],
                edges=[],
                analytics=None,
                message="No meaningful terms found in the provided text. Try providing more content.",
            )

        # 2. Run analytics
        analyzer = NetworkAnalysisService()
        analytics = analyzer.full_analysis(
            graph_data["nodes"], graph_data["edges"]
        )

        # 3. Optionally persist to Neo4j
        if request.persist:
            graph_service = GraphService()
            try:
                graph_service.create_cooccurrence_nodes(graph_data["nodes"])
                graph_service.create_cooccurrence_edges(graph_data["edges"])
            finally:
                graph_service.close()

        return TextInputResponse(
            nodes=graph_data["nodes"],
            edges=graph_data["edges"],
            analytics=analytics,
            message=f"Analyzed text: {len(graph_data['nodes'])} nodes, {len(graph_data['edges'])} edges.",
        )

    except Exception as e:
        logger.error(f"Text analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

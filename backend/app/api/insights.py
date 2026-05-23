"""
API endpoints for generating AI-powered graph insights.

All endpoints require a workspace_id query parameter to scope
analysis to one workspace's knowledge graph.

Provides:
  GET  /api/insights/?workspace_id=...            — Full structural insights
  GET  /api/insights/bridge?workspace_id=...      — Gap-bridging research questions
  GET  /api/insights/blind-spots?workspace_id=... — Missing topic identification
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any
from loguru import logger

from app.agents.state import ResearchState
from app.agents.insight_agent import (
    insight_agent_node,
    generate_gap_bridge_questions,
    generate_blind_spots,
)

router = APIRouter()


@router.get("/")
def get_insights(
    workspace_id: str = Query(..., description="Workspace ID to scope the graph analysis")
):
    """
    Analyzes the workspace Knowledge Graph using network science metrics
    and generates AI-powered structural insights.

    The LLM receives centrality rankings, community clusters, and structural
    gaps — not just basic node/edge counts.
    """
    try:
        initial_state = ResearchState(errors=[], workspace_id=workspace_id)
        result = insight_agent_node(initial_state)

        if result.get("errors"):
            raise Exception(" | ".join(result["errors"]))

        return {
            "workspace_id": workspace_id,
            "insights": result.get("insights", []),
        }
    except Exception as e:
        logger.error(f"Insight generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate insights: {str(e)}")


@router.get("/bridge")
def bridge_gap(
    workspace_id: str = Query(..., description="Workspace ID to scope the graph analysis"),
    gap_index: int = Query(default=0, ge=0, description="Index of the structural gap to bridge"),
):
    """
    Generate research questions that bridge a specific structural gap
    within the given workspace's knowledge graph.

    The LLM analyzes the disconnected clusters and proposes specific
    research questions referencing concepts from both sides.
    """
    try:
        result = generate_gap_bridge_questions(
            gap_index=gap_index,
            workspace_id=workspace_id,
        )

        if result.get("error"):
            raise Exception(result["error"])

        return result
    except Exception as e:
        logger.error(f"Bridge gap failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate bridge questions: {str(e)}")


@router.get("/blind-spots")
def find_blind_spots(
    workspace_id: str = Query(..., description="Workspace ID to scope the graph analysis")
):
    """
    Identify missing topics or perspectives in the workspace knowledge graph.

    The LLM examines the existing clusters and high-centrality nodes,
    then infers what topics/perspectives are absent but expected.
    """
    try:
        result = generate_blind_spots(workspace_id=workspace_id)

        if result.get("error"):
            raise Exception(result["error"])

        return result
    except Exception as e:
        logger.error(f"Blind spots failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to identify blind spots: {str(e)}")

"""
API endpoints for generating graph insights.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from app.agents.state import ResearchState
from app.agents.insight_agent import insight_agent_node

router = APIRouter()


@router.get("/", response_model=Dict[str, Any])
def generate_insights():
    """
    Analyzes the entire Knowledge Graph and generates AI insights.
    """
    try:
        # We can just call the node directly since it doesn't need a full workflow
        initial_state = ResearchState()
        result = insight_agent_node(initial_state)
        
        if result.get("errors"):
            raise Exception(" | ".join(result["errors"]))
            
        return {
            "insights": result.get("insights", [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate insights: {str(e)}")

"""
API endpoints for complex research queries.
"""

from fastapi import APIRouter, HTTPException

from app.models.schemas import QueryRequest, QueryResponse
from app.agents.workflows.research_workflow import build_research_workflow
from app.agents.state import ResearchState

router = APIRouter()
research_app = build_research_workflow()


@router.post("/", response_model=QueryResponse)
async def run_research_query(request: QueryRequest):
    """
    Run a complex research query.
    This triggers the planner, researcher, extraction, and report generator agents.
    """
    try:
        initial_state = ResearchState(
            query=request.query,
            workspace_id=str(request.workspace_id),   # ← scope to workspace
            errors=[]
        )
        
        # Run the research workflow
        final_state = await research_app.ainvoke(initial_state)

        if final_state.get("errors"):
            raise Exception(" | ".join(final_state["errors"]))

        report = final_state.get("report", "Report generation failed.")
        entities_found = len(final_state.get("entities", []))
        relationships_found = len(final_state.get("relationships", []))

        return QueryResponse(
            report=report,
            entities_found=entities_found,
            relationships_found=relationships_found
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

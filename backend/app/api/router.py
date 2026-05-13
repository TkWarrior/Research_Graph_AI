"""
Main API router — aggregates all sub-routers.
"""

from fastapi import APIRouter

api_router = APIRouter()


# Sub-routers will be included here as they are built:
from app.api.upload import router as upload_router
from app.api.query import router as query_router
from app.api.ask import router as ask_router
from app.api.graph import router as graph_router
from app.api.insights import router as insights_router
from app.api.sessions import router as sessions_router

api_router.include_router(upload_router, prefix="/upload", tags=["Upload"])
api_router.include_router(query_router, prefix="/query", tags=["Query"])
api_router.include_router(ask_router, prefix="/ask", tags=["Q&A"])
api_router.include_router(graph_router, prefix="/graph", tags=["Graph"])
api_router.include_router(insights_router, prefix="/insights", tags=["Insights"])
api_router.include_router(sessions_router, prefix="/sessions", tags=["Sessions"])


@api_router.get("/")
async def api_root():
    """API root — lists available endpoints."""
    return {
        "message": "Autonomous Multi-Agent Research System API",
        "endpoints": [
            "/api/health",
            "/api/upload",
            "/api/query",
            "/api/ask",
            "/api/graph",
            "/api/insights",
            "/api/sessions",
        ],
    }

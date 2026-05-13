"""
LangGraph workflow for deep research queries.
"""

from langgraph.graph import StateGraph, END
from app.agents.state import ResearchState
from app.agents.planner import planner_node
from app.agents.researcher import researcher_node
from app.agents.extraction import extraction_node
from app.agents.graph_builder import graph_builder_node
from app.agents.report_generator import report_generator_node


def build_research_workflow():
    """
    Builds the state graph for deep research.
    
    Flow:
    START -> planner -> researcher -> extraction -> graph_builder -> report_generator -> END
    """
    workflow = StateGraph(ResearchState)

    # Add nodes
    workflow.add_node("planner", planner_node)
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("extraction", extraction_node)
    workflow.add_node("graph_builder", graph_builder_node)
    workflow.add_node("report_generator", report_generator_node)

    # Define edges
    workflow.set_entry_point("planner")
    
    workflow.add_edge("planner", "researcher")
    workflow.add_edge("researcher", "extraction")
    workflow.add_edge("extraction", "graph_builder")
    
    # We can generate the report while the graph is building, or after.
    # Let's do it after to ensure everything is sequential and easy to debug.
    workflow.add_edge("graph_builder", "report_generator")
    workflow.add_edge("report_generator", END)

    # Compile the graph
    return workflow.compile()

"""
Agent for analyzing the knowledge graph using network science metrics
and generating AI-powered insights, gap-bridging questions, and blind spots.

InfraNodus-style: The LLM receives structural analysis (centrality,
communities, gaps) and generates insights based on the graph's topology.

All analysis is scoped to a workspace_id so insights are isolated
per workspace and never bleed across projects.
"""

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from loguru import logger

from app.agents.state import ResearchState
from app.services.graph_service import GraphService
from app.services.network_analysis_service import NetworkAnalysisService
from app.config import get_settings

settings = get_settings()

# ══════════════════════════════════════════════════════════════════════
# Prompts
# ══════════════════════════════════════════════════════════════════════

INSIGHT_PROMPT = """You are an expert graph data analyst specializing in text network analysis.
You are analyzing a knowledge graph built from research documents.

## Network Statistics
- Total Nodes: {node_count}
- Total Edges: {edge_count}
- Density: {density}
- Average Clustering Coefficient: {avg_clustering}
- Connected Components: {connected_components}
- Average Degree: {avg_degree}

## Topic Clusters (Communities Detected: {num_clusters}, Modularity: {modularity})
{clusters_description}

## Most Influential Bridge Nodes (Betweenness Centrality)
{centrality_description}

## Structural Gaps (Weakly Connected Cluster Pairs)
{gaps_description}

## Instructions
Based on this network structure analysis, provide:

1. **Core Topics Summary** (2-3 sentences): What are the main themes in this knowledge base?
2. **Key Bridge Concepts** (2-3 bullet points): Which nodes bridge different topics, and why are they important?
3. **Structural Insights** (2-3 bullet points): What does the network topology reveal? (e.g., is the graph fragmented or densely connected? Are there isolated clusters?)
4. **Research Gaps** (2-3 bullet points): Based on the structural gaps, what questions or areas are underexplored?
5. **Recommendations** (2-3 bullet points): What new connections or investigations should be explored?

Format your response as structured Markdown with the section headers above."""


GAP_BRIDGE_PROMPT = """You are an expert research advisor analyzing structural gaps in a knowledge graph.

Two topic clusters in the knowledge graph are disconnected or weakly connected:

**Cluster A** (main concepts): {cluster_a_nodes}
**Cluster B** (main concepts): {cluster_b_nodes}

Current connections between these clusters: {inter_edges} edges

## Task
Generate 3 specific research questions that would bridge these two clusters.
Each question should:
1. Reference specific concepts from BOTH clusters
2. Propose a plausible connection or investigation
3. Be actionable and specific (not generic)

Format as a numbered list."""


BLIND_SPOTS_PROMPT = """You are an expert research advisor analyzing a knowledge graph for blind spots.

## The Knowledge Graph Contains These Topic Clusters:
{clusters_summary}

## The Most Important Concepts Are:
{top_concepts}

## The Network Has These Characteristics:
- {node_count} concepts, {edge_count} connections
- {num_clusters} topic clusters
- Density: {density} ({density_description})

## Task
Identify 3-5 potential blind spots — topics, perspectives, or connections that are MISSING from this knowledge base but would be expected given the existing topics. 

For each blind spot:
1. Name the missing topic/perspective
2. Explain which existing clusters it would connect to
3. Suggest why it matters

Format as a numbered Markdown list."""


# ══════════════════════════════════════════════════════════════════════
# Service Functions
# ══════════════════════════════════════════════════════════════════════

def _get_llm():
    return ChatGroq(
        model=settings.LLM_MODEL,
        api_key=settings.GROQ_API_KEY,
        temperature=0.4,
        max_retries=2
    )


def _run_analysis(workspace_id: str = None):
    """
    Fetch graph data for the given workspace and run full network analysis.

    workspace_id is required for production use. Omitting it causes the
    global Neo4j graph to be analysed (all workspaces merged) which is
    only acceptable in single-user / dev environments.
    """
    graph_service = GraphService()
    try:
        # Pass workspace_id so only this workspace's nodes/edges are loaded
        data = graph_service.get_full_graph(limit=1000, workspace_id=workspace_id)
    finally:
        graph_service.close()

    if not data["nodes"]:
        return None, None

    analyzer = NetworkAnalysisService()
    analysis = analyzer.full_analysis(data["nodes"], data["edges"])
    return data, analysis


def _format_clusters(analysis):
    """Format cluster info for prompts."""
    clusters = analysis.get("communities", {}).get("clusters", [])
    if not clusters:
        return "No clusters detected."
    
    lines = []
    for c in clusters:
        top = c.get("members", [])[:5]
        lines.append(f"- Cluster {c['id']+1} ({c['size']} nodes): {', '.join(top)}")
    return "\n".join(lines)


def _format_centrality(analysis):
    """Format centrality rankings for prompts."""
    centrality = analysis.get("centrality", [])
    if not centrality:
        return "No centrality data available."
    
    lines = []
    for i, item in enumerate(centrality[:10]):
        lines.append(f"{i+1}. **{item['name']}** (centrality: {item['centrality']:.4f})")
    return "\n".join(lines)


def _format_gaps(analysis):
    """Format structural gaps for prompts."""
    gaps = analysis.get("gaps", [])
    if not gaps:
        return "No structural gaps detected — the graph appears well-connected."
    
    lines = []
    for gap in gaps:
        a_nodes = ", ".join(gap["cluster_a"]["top_nodes"])
        b_nodes = ", ".join(gap["cluster_b"]["top_nodes"])
        strength = "DISCONNECTED" if gap["gap_strength"] == "strong" else f"{gap['inter_edges']} weak edges"
        lines.append(f"- [{a_nodes}] ↔ [{b_nodes}] — {strength}")
    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════
# Agent Node (for LangGraph workflows)
# ══════════════════════════════════════════════════════════════════════

def insight_agent_node(state: ResearchState) -> dict:
    """Analyzes the workspace knowledge graph and generates AI-powered insights."""
    workspace_id = state.get("workspace_id")   # scope this analysis to one workspace

    if not workspace_id:
        logger.warning("insight_agent_node called without workspace_id — analysing global graph.")

    data, analysis = _run_analysis(workspace_id=workspace_id)
    
    if analysis is None:
        return {"insights": ["No graph data available to analyze."], "current_step": "insight_generation_empty"}

    stats = analysis.get("stats", {})
    communities = analysis.get("communities", {})

    try:
        llm = _get_llm()
        prompt = ChatPromptTemplate.from_template(INSIGHT_PROMPT)
        chain = prompt | llm

        response = chain.invoke({
            "node_count": stats.get("node_count", 0),
            "edge_count": stats.get("edge_count", 0),
            "density": stats.get("density", 0),
            "avg_clustering": stats.get("avg_clustering", 0),
            "connected_components": stats.get("connected_components", 0),
            "avg_degree": stats.get("avg_degree", 0),
            "num_clusters": len(communities.get("clusters", [])),
            "modularity": communities.get("modularity", 0),
            "clusters_description": _format_clusters(analysis),
            "centrality_description": _format_centrality(analysis),
            "gaps_description": _format_gaps(analysis),
        })
        
        return {
            "insights": [response.content],
            "current_step": "insight_generation_complete"
        }
    except Exception as e:
        logger.error(f"Insight generation failed: {e}")
        return {"errors": [f"Insight generation failed: {str(e)}"]}


# ══════════════════════════════════════════════════════════════════════
# Standalone Functions (called directly by API, not via LangGraph)
# ══════════════════════════════════════════════════════════════════════

def generate_gap_bridge_questions(gap_index: int = 0, workspace_id: str = None):
    """
    Generate research questions to bridge a specific structural gap.
    workspace_id scopes the analysis to one workspace.
    """
    data, analysis = _run_analysis(workspace_id=workspace_id)
    if analysis is None:
        return {"questions": [], "error": "No graph data available."}

    gaps = analysis.get("gaps", [])
    if not gaps:
        return {"questions": [], "message": "No structural gaps found — the graph is well-connected."}

    if gap_index >= len(gaps):
        gap_index = 0
    
    gap = gaps[gap_index]

    try:
        llm = _get_llm()
        prompt = ChatPromptTemplate.from_template(GAP_BRIDGE_PROMPT)
        chain = prompt | llm

        response = chain.invoke({
            "cluster_a_nodes": ", ".join(gap["cluster_a"]["top_nodes"]),
            "cluster_b_nodes": ", ".join(gap["cluster_b"]["top_nodes"]),
            "inter_edges": gap["inter_edges"],
        })

        return {
            "questions": response.content,
            "gap": gap,
        }
    except Exception as e:
        logger.error(f"Gap bridge generation failed: {e}")
        return {"questions": [], "error": str(e)}


def generate_blind_spots(workspace_id: str = None):
    """
    Identify missing topics or perspectives in the knowledge graph.
    workspace_id scopes the analysis to one workspace.
    """
    data, analysis = _run_analysis(workspace_id=workspace_id)
    if analysis is None:
        return {"blind_spots": "", "error": "No graph data available."}

    stats = analysis.get("stats", {})
    communities = analysis.get("communities", {})
    centrality = analysis.get("centrality", [])

    try:
        llm = _get_llm()
        prompt = ChatPromptTemplate.from_template(BLIND_SPOTS_PROMPT)
        chain = prompt | llm

        density = stats.get("density", 0)
        density_desc = "sparse" if density < 0.1 else "moderate" if density < 0.3 else "dense"

        response = chain.invoke({
            "clusters_summary": _format_clusters(analysis),
            "top_concepts": ", ".join([c["name"] for c in centrality[:15]]),
            "node_count": stats.get("node_count", 0),
            "edge_count": stats.get("edge_count", 0),
            "num_clusters": len(communities.get("clusters", [])),
            "density": density,
            "density_description": density_desc,
        })

        return {"blind_spots": response.content}
    except Exception as e:
        logger.error(f"Blind spots generation failed: {e}")
        return {"blind_spots": "", "error": str(e)}

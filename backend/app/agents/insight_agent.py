"""
Agent for analyzing the knowledge graph and extracting high-level insights.
"""

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

from app.agents.state import ResearchState
from app.services.graph_service import GraphService
from app.config import get_settings

settings = get_settings()

INSIGHT_PROMPT = """You are an expert graph data analyst.
Analyze the following knowledge graph statistics and structure to provide 3-5 high-level, actionable insights.

Graph Statistics:
- Total Nodes (Entities): {node_count}
- Total Edges (Relationships): {edge_count}

Most Connected Entities (Hubs):
{top_entities}

Instructions:
1. Identify the core themes of this graph based on the most connected entities.
2. What are the most important relationships?
3. Format the insights as a bulleted Markdown list.

Insights:"""

prompt_template = ChatPromptTemplate.from_template(INSIGHT_PROMPT)


def insight_agent_node(state: ResearchState) -> dict:
    """Analyzes the overall knowledge graph to provide insights."""
    
    graph_service = GraphService()
    
    try:
        stats = graph_service.get_graph_stats()
        
        # Format top entities for prompt
        top_entities_str = ""
        for i, item in enumerate(stats.get("most_connected", [])):
            top_entities_str += f"{i+1}. {item['name']} (Connections: {item['degree']})\n"
            
        if not top_entities_str:
            top_entities_str = "No entities found."

        llm = ChatGroq(
            model=settings.LLM_MODEL,
            api_key=settings.GROQ_API_KEY,
            temperature=0.4
        )
        
        chain = prompt_template | llm
        
        response = chain.invoke({
            "node_count": stats.get("node_count", 0),
            "edge_count": stats.get("edge_count", 0),
            "top_entities": top_entities_str
        })
        
        return {
            "insights": [response.content],
            "current_step": "insight_generation_complete"
        }
    except Exception as e:
        return {"errors": [f"Insight generation failed: {str(e)}"]}
    finally:
        graph_service.close()

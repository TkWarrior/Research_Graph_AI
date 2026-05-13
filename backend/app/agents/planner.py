"""
Agent for breaking down a complex research query into subtopics.
"""

from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

from app.agents.state import ResearchState
from app.config import get_settings

settings = get_settings()

class Subtopics(BaseModel):
    topics: list[str] = Field(description="A list of 2 to 4 specific subtopics to research.")


def planner_node(state: ResearchState) -> dict:
    """Analyzes the user query and generates subtopics for research."""
    query = state.get("query")
    
    if not query:
        return {"errors": ["No query provided for the planner."]}

    llm = ChatGroq(
        model=settings.LLM_MODEL,
        api_key=settings.GROQ_API_KEY,
        temperature=0
    )
    
    structured_llm = llm.with_structured_output(Subtopics)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a research planner. Break down the user's main research query into 2-4 distinct, highly specific subtopics or questions that need to be investigated to provide a comprehensive answer."),
        ("human", "{query}")
    ])
    
    chain = prompt | structured_llm
    
    try:
        result = chain.invoke({"query": query})
        return {
            "subtopics": result.topics,
            "current_step": "planning_complete"
        }
    except Exception as e:
        return {"errors": [f"Planner failed: {str(e)}"]}

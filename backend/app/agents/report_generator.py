"""
Agent for generating structured reports from researched context.
"""

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

from app.agents.state import ResearchState
from app.config import get_settings

settings = get_settings()

REPORT_PROMPT = """You are an expert research analyst. 
Generate a comprehensive, structured Markdown report answering the user's main query based on the researched context.

Main Query: {query}
Subtopics Researched: {subtopics}

Context (from semantic search and entity extraction):
{context}

Instructions:
1. Structure the report with a Title, Executive Summary, Detailed Findings (by subtopic), and Conclusion.
2. Rely strictly on the provided Context. Do not hallucinate outside information.
3. Use Markdown formatting heavily (headers, bolding, lists).
4. If the context is insufficient, state exactly what is missing.

Report:"""

prompt_template = ChatPromptTemplate.from_template(REPORT_PROMPT)


def report_generator_node(state: ResearchState) -> dict:
    """Generates a structured research report."""
    query = state.get("query")
    subtopics = state.get("subtopics", [])
    chunk_texts = state.get("chunk_texts", [])
    
    # Format context
    context = "\n\n".join(chunk_texts)
    
    if not context.strip():
        context = "No information could be retrieved for this query."

    llm = ChatGroq(
        model=settings.LLM_MODEL,
        api_key=settings.GROQ_API_KEY,
        temperature=0.3
    )
    
    chain = prompt_template | llm
    
    try:
        response = chain.invoke({
            "query": query,
            "subtopics": ", ".join(subtopics),
            "context": context
        })
        
        return {
            "report": response.content,
            "current_step": "report_generation_complete"
        }
    except Exception as e:
        return {"errors": [f"Report generation failed: {str(e)}"]}

"""
Agent for merging contexts and generating the final answer.
"""

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

from app.agents.state import ResearchState
from app.config import get_settings

settings = get_settings()

HYBRID_RAG_PROMPT = """You are a highly intelligent research assistant. 
You are tasked with answering the user's question based on the provided context.

The context comes from two sources:
1. Semantic Document Search (exact text chunks from the document)
2. Knowledge Graph (relationships and facts extracted from the document)

Context:
{context}

Question: {query}

Instructions:
1. Answer the question clearly and thoroughly using ONLY the provided context.
2. If the context does not contain the answer, politely say that you cannot answer based on the current documents.
3. Synthesize information from both the document chunks and the knowledge graph.
4. Use formatting (bullet points, bold text) to make your answer easy to read.

Answer:"""

prompt_template = ChatPromptTemplate.from_template(HYBRID_RAG_PROMPT)


def hybrid_rag_node(state: ResearchState) -> dict:
    """Merges vector and graph contexts and generates an answer."""
    query = state.get("query")
    vector_context = state.get("vector_context", [])
    graph_context = state.get("graph_context", [])

    # 1. Format the Merged Context
    merged_context = ""
    
    if vector_context:
        merged_context += "=== Document Context ===\n"
        for i, chunk in enumerate(vector_context):
            merged_context += f"[Doc Chunk {i+1} (Score: {chunk.get('relevance_score', 0):.2f})]:\n"
            merged_context += f"{chunk.get('content')}\n\n"
            
    if graph_context:
        merged_context += "=== Knowledge Graph Context ===\n"
        for item in graph_context:
            entity = item["entity"]
            edges = item["subgraph"]["edges"]
            merged_context += f"Entity '{entity}' relationships:\n"
            for edge in edges:
                merged_context += f"- {edge['source']} [{edge['type']}] -> {edge['target']} ({edge['description']})\n"
            merged_context += "\n"

    if not merged_context.strip():
        merged_context = "No relevant context found."

    # 2. Generate the Answer
    llm = ChatGroq(
        model=settings.LLM_MODEL,
        api_key=settings.GROQ_API_KEY,
        temperature=0.2
    )
    
    chain = prompt_template | llm
    
    try:
        response = chain.invoke({
            "context": merged_context,
            "query": query
        })
        
        return {
            "merged_context": merged_context,
            "answer": response.content,
            "current_step": "hybrid_rag_complete"
        }
    except Exception as e:
        return {"errors": [f"Hybrid RAG generation failed: {str(e)}"]}

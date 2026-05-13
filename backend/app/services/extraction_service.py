"""
Service for extracting entities and relationships from text using an LLM.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
import asyncio

from app.config import get_settings

settings = get_settings()

# ══════════════════════════════════════════════════════════════════════
# Extraction Schemas
# ══════════════════════════════════════════════════════════════════════

class Entity(BaseModel):
    name: str = Field(description="The normalized, specific name of the entity.")
    type: str = Field(
        description="The type of the entity (e.g., PERSON, ORGANIZATION, CONCEPT, TECHNOLOGY, LOCATION, EVENT)."
    )
    description: str = Field(description="A brief description or context of the entity found in the text.")

class Relationship(BaseModel):
    source: str = Field(description="The exact name of the source entity.")
    target: str = Field(description="The exact name of the target entity.")
    type: str = Field(
        description="The nature of the relationship (e.g., RELATED_TO, PART_OF, USES, CREATED_BY, INFLUENCES)."
    )
    description: str = Field(description="A brief explanation of how the two entities are related.")

class ExtractionResult(BaseModel):
    entities: List[Entity] = Field(description="List of all extracted entities.", default_factory=list)
    relationships: List[Relationship] = Field(description="List of relationships between the extracted entities.", default_factory=list)


# ══════════════════════════════════════════════════════════════════════
# Extraction Prompts
# ══════════════════════════════════════════════════════════════════════

EXTRACTION_SYSTEM_PROMPT = """You are an expert knowledge graph extraction system. 
Your task is to analyze the given text chunk and extract meaningful entities and the relationships between them.

# Guidelines for Entities:
1. Extract specific, concrete entities (People, Organizations, Technologies, Concepts, Locations, Events).
2. Normalize names to their most recognizable form (e.g., "Artificial Intelligence" instead of "AI" if both refer to the same thing).
3. Do not extract overly generic terms or stop words.
4. Provide a concise description based ONLY on the provided text.

# Guidelines for Relationships:
1. Relationships must exist strictly between the extracted entities.
2. The 'source' and 'target' MUST match the 'name' of an extracted entity exactly.
3. Keep the relationship 'type' concise and uppercase (e.g., USES, DEVELOPED_BY, PART_OF).
4. Provide a brief explanation of the relationship based on the text.

Do not hallucinate. If no entities or relationships are found, return empty lists."""

EXTRACTION_PROMPT_TEMPLATE = ChatPromptTemplate.from_messages([
    ("system", EXTRACTION_SYSTEM_PROMPT),
    ("human", "Text to analyze:\n\n{text}")
])


class ExtractionService:
    """Uses LLM to extract entities and relationships from text."""

    def __init__(self):
        # Initialize Groq LLM
        self.llm = ChatGroq(
            model=settings.LLM_MODEL,
            api_key=settings.GROQ_API_KEY,
            temperature=0, # Use 0 for more deterministic, structured extraction
            max_retries=3
        )
        
        # Bind the Pydantic schema to the LLM
        self.structured_llm = self.llm.with_structured_output(ExtractionResult)
        
        # Create the extraction chain
        self.extraction_chain = EXTRACTION_PROMPT_TEMPLATE | self.structured_llm

    async def extract_from_text(self, text: str) -> ExtractionResult:
        """Extract entities and relationships from a single piece of text."""
        if len(text.strip()) < 50:
            return ExtractionResult(entities=[], relationships=[])
            
        try:
            result = await self.extraction_chain.ainvoke({"text": text})
            return result
        except Exception as e:
            print(f"Extraction failed: {e}")
            return ExtractionResult(entities=[], relationships=[])

    async def extract_from_chunks(self, texts: List[str], max_concurrency: int = 5) -> ExtractionResult:
        """Process multiple chunks concurrently and merge the results."""
        semaphore = asyncio.Semaphore(max_concurrency)

        async def process_with_semaphore(text):
            async with semaphore:
                return await self.extract_from_text(text)

        # Run extraction concurrently
        tasks = [process_with_semaphore(t) for t in texts]
        results = await asyncio.gather(*tasks)

        # Merge results
        merged_result = ExtractionResult()
        
        # Simple merging (deduplication will be handled later by the Knowledge Graph builder)
        for res in results:
            if res:
                merged_result.entities.extend(res.entities)
                merged_result.relationships.extend(res.relationships)

        return merged_result

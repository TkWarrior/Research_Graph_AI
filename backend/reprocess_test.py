import asyncio
import app.models
from app.database import SessionLocal
from app.models.document import Document
from app.agents.workflows.document_workflow import build_document_workflow
from app.agents.state import ResearchState

async def reprocess():
    db = SessionLocal()
    doc = db.query(Document).first()
    if not doc:
        print("No doc found")
        return
    
    print("Re-processing:", doc.original_filename)
    doc.status = "processing"
    doc.error_message = None
    db.commit()
    
    app = build_document_workflow()
    state = ResearchState(
        document_id=str(doc.id),
        file_path="./uploads/" + doc.filename,
        file_type=doc.file_type,
        errors=[]
    )
    
    try:
        result = await app.ainvoke(state)
        errors = result.get("errors", [])
        if errors:
            print("ERRORS:", errors)
            doc.status = "failed"
            doc.error_message = " | ".join(errors)
        else:
            ent = len(result.get("entities", []))
            rel = len(result.get("relationships", []))
            chunks = len(result.get("chunks", []))
            print("SUCCESS! Entities:", ent, "Relationships:", rel, "Chunks:", chunks)
            doc.status = "completed"
            doc.entity_count = ent
            doc.relationship_count = rel
            doc.chunk_count = chunks
    except Exception as e:
        print("EXCEPTION:", e)
        import traceback
        traceback.print_exc()
        doc.status = "failed"
        doc.error_message = str(e)
    
    db.commit()
    db.close()

asyncio.run(reprocess())

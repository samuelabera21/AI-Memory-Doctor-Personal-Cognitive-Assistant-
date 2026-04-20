from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.db.database import SessionLocal
from app.models.memory_model import Memory

from app.services.nlp_service import structure_memory_text
from app.services.embedding_service import get_embedding
from app.services.vector_store import upsert_memory_vector
from app.services.dependency import get_current_user

router = APIRouter()


class MemoryInput(BaseModel):
    content: str
    time: str | None = None


@router.post("/add-memory")
def add_memory(memory: MemoryInput, user=Depends(get_current_user)):
    content = memory.content.strip()

    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Memory content cannot be empty")

    if content.endswith("?"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This looks like a question, not a memory")

    structured = structure_memory_text(text=content, fallback_time=memory.time)
    structured_memory = {
        "user_id": user.id,
        "date": structured["date"],
        "time": structured["time"],
        "type": structured["type"],
        "content": structured["content"],
        "duration": structured["duration"],
        "tags": ",".join(structured["tags"]),
        "source_text": structured["source_text"],
        "version": 1,
        "is_active": 1,
        "is_deleted": 0,
    }

    db = SessionLocal()

    try:
        db_memory = Memory(**structured_memory)
        db.add(db_memory)
        db.commit()
        db.refresh(db_memory)

        vector = get_embedding(content)
        upsert_memory_vector(
            memory_id=db_memory.id,
            user_id=user.id,
            vector=vector,
            text=db_memory.content,
        )

    finally:
        db.close()

    return {
        "status": "saved",
        "memory_id": db_memory.id,
        "data": structured_memory
    }
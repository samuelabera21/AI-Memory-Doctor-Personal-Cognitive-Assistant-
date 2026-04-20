from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.db.database import SessionLocal
from app.models.memory_model import Memory
from app.services.dependency import get_current_user
from app.services.summarization_service import summarize_memories, get_date_range

router = APIRouter()


class SummaryInput(BaseModel):
    query: str


@router.post("/summarize")
def summarize(data: SummaryInput, user=Depends(get_current_user)):
    db = SessionLocal()

    try:
        start, end = get_date_range(data.query)

        if not start:
            return {"message": "Invalid time range"}

        memories = db.query(Memory).filter(
            Memory.user_id == user.id,
            Memory.is_active == 1,
            Memory.is_deleted == 0,
            Memory.date >= start,
            Memory.date <= end
        ).all()

        summary = summarize_memories(memories)

        return {
            "query": data.query,
            "summary": summary,
            "count": len(memories),
            "period": {
                "start_date": start,
                "end_date": end,
            }
        }

    finally:
        db.close()
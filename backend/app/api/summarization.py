from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.db.database import SessionLocal
from app.models.memory_model import Memory
from app.services.importance_service import compute_importance_score, explain_importance
from app.services.dependency import get_current_user
from app.services.llm_service import generate_grounded_answer
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

        memory_rows = [
            {
                "date": m.date,
                "time": m.time,
                "type": m.type,
                "content": m.content,
                "duration": m.duration,
                "tags": m.tags.split(",") if m.tags else [],
                "version": m.version,
                "importance_score": compute_importance_score(m),
                "importance_reasons": explain_importance(m),
            }
            for m in memories
        ]

        ai_summary = generate_grounded_answer(query=data.query, memory_rows=memory_rows)
        ai_used = bool(ai_summary)
        summary = ai_summary if ai_used else summarize_memories(memories)

        return {
            "query": data.query,
            "summary": summary,
            "count": len(memories),
            "ai_used": ai_used,
            "provider": "gemini" if ai_used else "fallback",
            "period": {
                "start_date": start,
                "end_date": end,
            }
        }

    finally:
        db.close()
from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime

from app.db.database import SessionLocal
from app.models.memory_model import Memory

router = APIRouter()


class QueryInput(BaseModel):
    query: str


@router.post("/search-memory")
def search_memory(data: QueryInput):
    db = SessionLocal()

    query_text = data.query.lower()

    # TEMP LOGIC (we will improve later)
    today = datetime.now().strftime("%Y-%m-%d")

    results = []

    if "today" in query_text:
        results = db.query(Memory).filter(Memory.date == today).all()
    else:
        results = db.query(Memory).all()

    return {
        "results": [
            {
                "date": m.date,
                "time": m.time,
                "type": m.type,
                "content": m.content,
                "duration": m.duration,
                "tags": m.tags
            }
            for m in results
        ]
    }
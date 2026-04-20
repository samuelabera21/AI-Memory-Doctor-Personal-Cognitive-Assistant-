from fastapi import APIRouter
from pydantic import BaseModel

from app.db.database import SessionLocal
from app.models.memory_model import Memory

router = APIRouter()


class UpdateInput(BaseModel):
    old_text: str
    new_text: str


@router.post("/update-memory")
def update_memory(data: UpdateInput):
    db = SessionLocal()

    try:
        # 🔍 STEP 1: find memory
        memory = db.query(Memory).filter(
            Memory.content == data.old_text
        ).first()

        if not memory:
            return {"message": "Memory not found"}

        # ✏️ STEP 2: update content
        memory.content = data.new_text

        db.commit()

        return {
            "status": "updated",
            "old": data.old_text,
            "new": data.new_text
        }

    finally:
        db.close()
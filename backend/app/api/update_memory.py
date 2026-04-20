from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.db.database import SessionLocal
from app.services.dependency import get_current_user
from app.services.update_service import find_memory_to_update

router = APIRouter()


class UpdateInput(BaseModel):
    text: str


@router.post("/update-memory")
def update_memory(data: UpdateInput, user=Depends(get_current_user)):
    db = SessionLocal()

    try:
        text = data.text.lower()

        # ❗ extract new content (simple rule)
        if "not" not in text:
            return {"message": "No correction detected"}

        parts = text.split("not")

        new_part = parts[0].replace("actually", "").strip()
        old_part = parts[1].strip()

        memory = find_memory_to_update(old_part, db, user.id)

        if not memory:
            return {"message": "No matching memory found"}

        # ✅ update
        memory.content = new_part
        db.commit()

        return {
            "message": "Memory updated",
            "updated": memory.content
        }

    finally:
        db.close()
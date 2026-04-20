from fastapi import APIRouter, Depends

from app.db.database import SessionLocal
from app.models.memory_model import Memory
from app.services.dependency import get_current_user
from app.services.insight_service import analyze_insights

router = APIRouter()


@router.get("/insights")
def get_insights(user=Depends(get_current_user)):
    db = SessionLocal()

    try:
        memories = db.query(Memory).filter(
            Memory.user_id == user.id,
            Memory.is_active == 1,
            Memory.is_deleted == 0,
        ).all()

        result = analyze_insights(memories)

        return {
            "count": len(memories),
            **result,
        }

    finally:
        db.close()
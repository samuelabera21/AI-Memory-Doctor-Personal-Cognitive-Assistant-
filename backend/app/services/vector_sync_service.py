from app.db.database import SessionLocal
from app.models.memory_model import Memory

from app.services.embedding_service import get_embedding
from app.services.vector_store import reset_index, upsert_memory_vector


def rebuild_faiss_index():
    db = SessionLocal()

    try:
        memories = db.query(Memory).filter(
            Memory.is_active == 1,
            Memory.is_deleted == 0,
        ).all()
        reset_index()

        for m in memories:
            upsert_memory_vector(
                memory_id=m.id,
                user_id=m.user_id,
                vector=get_embedding(m.content),
                text=m.content,
            )
    finally:
        db.close()
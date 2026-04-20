from app.services.embedding_service import get_embedding
from app.services.vector_store import search_vector


def find_memory_to_update(query_text, db, user_id):
    query_vector = get_embedding(query_text)

    similar = search_vector(query_vector, k=1)

    if not similar:
        return None

    from app.models.memory_model import Memory

    memory = db.query(Memory).filter(
        Memory.user_id == user_id,
        Memory.content == similar[0]
    ).first()

    return memory
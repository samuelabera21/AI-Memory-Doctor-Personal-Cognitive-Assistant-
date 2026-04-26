from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.db.database import SessionLocal
from app.models.memory_model import Memory

from app.services.embedding_service import get_embedding
from app.services.vector_store import search_user_vectors
from app.services.answer_service import generate_answer
from app.services.temporal_service import parse_query_time_filters, in_time_window
from app.services.ranking_service import rank_memories
from app.services.semantic_intent_service import detect_requested_types_semantic
from app.services.conversation_service import update_context

from app.services.dependency import get_current_user

router = APIRouter()


class SearchInput(BaseModel):
    query: str


def _extract_requested_types(query: str) -> set[str]:
    q = query.lower()
    requested = set()
    if "summarize" in q or "summary" in q:
        return requested

    mapping = {
        "activity": ["activity", "activities", "learn", "learned", "study", "studied"],
        "decision": ["decision", "decisions", "decide", "planned"],
        "goal": ["goal", "goals", "aim"],
        "habit": ["habit", "habits", "routine"],
        "mistake": ["mistake", "mistakes", "wrong"],
        "event": ["event", "events", "attended"],
        "idea": ["idea", "ideas", "brainstorm"],
        "emotion": ["emotion", "emotions", "felt", "feeling"],
    }
    for category, terms in mapping.items():
        if any(term in q for term in terms):
            requested.add(category)

    # Goals and decisions are often phrased interchangeably in memory queries.
    if "goal" in requested:
        requested.add("decision")
    if "decision" in requested:
        requested.add("goal")

    return requested


def _extract_requested_types_intelligent(query: str) -> set[str]:
    semantic = detect_requested_types_semantic(query)
    keyword = _extract_requested_types(query)
    return semantic.union(keyword)


@router.post("/search-memory")
def search_memory(data: SearchInput, user=Depends(get_current_user)):
    db = SessionLocal()

    try:
        time_filters = parse_query_time_filters(data.query)
        query_vector = get_embedding(data.query)
        vector_results = search_user_vectors(query_vector=query_vector, user_id=user.id, k=20)
        semantic_scores = {row["memory_id"]: row["semantic_score"] for row in vector_results}

        memory_ids = [row["memory_id"] for row in vector_results]
        requested_types = _extract_requested_types_intelligent(data.query)
        has_structured_time = bool(time_filters.get("start_date") or time_filters.get("end_date") or time_filters.get("start_time"))

        if has_structured_time or requested_types:
            memories = db.query(Memory).filter(
                Memory.user_id == user.id,
                Memory.is_active == 1,
                Memory.is_deleted == 0,
            ).all()
        elif memory_ids:
            memories = db.query(Memory).filter(
                Memory.user_id == user.id,
                Memory.is_active == 1,
                Memory.is_deleted == 0,
                Memory.id.in_(memory_ids),
            ).all()
        else:
            memories = db.query(Memory).filter(
                Memory.user_id == user.id,
                Memory.is_active == 1,
                Memory.is_deleted == 0,
            ).all()
        filtered = []
        for m in memories:
            if time_filters.get("start_date") and m.date < time_filters["start_date"]:
                continue
            if time_filters.get("end_date") and m.date > time_filters["end_date"]:
                continue
            if not in_time_window(m.time, time_filters.get("start_time"), time_filters.get("end_time")):
                continue
            if requested_types and m.type not in requested_types:
                continue
            filtered.append(m)

        ranked = rank_memories(query=data.query, memories=filtered, semantic_scores=semantic_scores)
        if "summarize" in data.query.lower() or "recent" in data.query.lower():
            final_results = sorted(filtered, key=lambda m: (m.date, m.time), reverse=True)[:8]
        else:
            final_results = ranked[:8]
        answer = generate_answer(data.query, final_results)

        update_context(data.query, final_results)

        return {
            "query": data.query,
            "answer": answer,
            "results": [
                {
                    "id": m.id,
                    "content": m.content,
                    "type": m.type,
                    "date": m.date,
                    "time": m.time,
                    "duration": m.duration,
                    "semantic_score": semantic_scores.get(m.id, 0.0),
                }
                for m in final_results
            ],
            "time_filters": time_filters,
        }

    finally:
        db.close()
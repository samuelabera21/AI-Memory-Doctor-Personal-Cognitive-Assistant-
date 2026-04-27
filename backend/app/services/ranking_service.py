from datetime import datetime
import re

from app.services.importance_service import compute_importance_score


def _days_since(date_str: str) -> int:
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
        return max(0, (datetime.now() - d).days)
    except (ValueError, TypeError):
        return 999


def _token_overlap(query: str, content: str) -> float:
    q = set(re.findall(r"\b[a-zA-Z]{2,}\b", query.lower()))
    c = set(re.findall(r"\b[a-zA-Z]{2,}\b", content.lower()))
    if not q or not c:
        return 0.0
    return len(q.intersection(c)) / max(1, len(q))


def score_memory(query: str, memory, semantic_score: float = 0.0):
    overlap = _token_overlap(query, memory.content)
    recency = 1.0 / (1.0 + _days_since(memory.date))
    importance = compute_importance_score(memory)

    semantic_weight = 0.60
    overlap_weight = 0.20
    recency_weight = 0.20
    importance_weight = 0.20

    score = (
        semantic_weight * semantic_score
        + overlap_weight * overlap
        + recency_weight * recency
        + importance_weight * importance
    )

    if memory.type == "mistake" and any(w in query.lower() for w in ["mistake", "repeat"]):
        score += 0.15

    return score


def rank_memories(query: str, memories, semantic_scores: dict[int, float] | None = None):
    semantic_scores = semantic_scores or {}
    scored = []

    for m in memories:
        score = score_memory(query=query, memory=m, semantic_score=semantic_scores.get(m.id, 0.0))
        scored.append((score, m))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [m for _, m in scored]
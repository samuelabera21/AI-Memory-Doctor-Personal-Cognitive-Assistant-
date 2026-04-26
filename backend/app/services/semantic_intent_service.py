from __future__ import annotations

from functools import lru_cache

from app.services.embedding_service import get_embedding


TYPE_PROTOTYPES: dict[str, list[str]] = {
    "activity": [
        "things I did",
        "actions I performed",
        "study and work activities",
    ],
    "decision": [
        "choices I made",
        "plans and decisions",
        "things I decided",
    ],
    "goal": [
        "goals and targets",
        "things I want to achieve",
        "future objectives",
    ],
    "habit": [
        "repeated routines",
        "daily habits",
        "usual behavior",
    ],
    "mistake": [
        "errors I made",
        "things I did wrong",
        "repeated mistakes",
    ],
    "event": [
        "events I attended",
        "occasions and meetings",
        "important happenings",
    ],
    "idea": [
        "ideas and thoughts",
        "brainstorm concepts",
        "new concepts I thought about",
    ],
    "emotion": [
        "how I felt",
        "emotions and mood",
        "feelings I experienced",
    ],
}


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(y * y for y in b) ** 0.5
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


@lru_cache(maxsize=1)
def _prototype_vectors() -> dict[str, list[list[float]]]:
    vectors: dict[str, list[list[float]]] = {}
    for memory_type, examples in TYPE_PROTOTYPES.items():
        vectors[memory_type] = [get_embedding(example) for example in examples]
    return vectors


def detect_requested_types_semantic(query: str, threshold: float = 0.36) -> set[str]:
    q = (query or "").strip()
    if not q:
        return set()

    query_vector = get_embedding(q)
    vectors = _prototype_vectors()
    scores: dict[str, float] = {}

    for memory_type, prototype_list in vectors.items():
        best = max(_cosine_similarity(query_vector, prototype) for prototype in prototype_list)
        scores[memory_type] = best

    selected = {memory_type for memory_type, score in scores.items() if score >= threshold}

    # Keep closely-related categories together when one is requested.
    if "goal" in selected:
        selected.add("decision")
    if "decision" in selected:
        selected.add("goal")

    return selected


def get_semantic_type_scores(query: str) -> dict[str, float]:
    q = (query or "").strip()
    if not q:
        return {}

    query_vector = get_embedding(q)
    vectors = _prototype_vectors()
    scores: dict[str, float] = {}

    for memory_type, prototype_list in vectors.items():
        best = max(_cosine_similarity(query_vector, prototype) for prototype in prototype_list)
        scores[memory_type] = best

    return scores


def is_confident_type_query(query: str, semantic_scores: dict[str, float], min_confidence: float = 0.52) -> bool:
    q = (query or "").lower()
    # Explicit type-focused query should always allow type filtering.
    explicit_signals = [
        "activity", "activities", "decision", "decisions", "goal", "goals",
        "habit", "habits", "mistake", "mistakes", "event", "events", "idea", "ideas",
        "what type", "what category",
    ]
    if any(signal in q for signal in explicit_signals):
        return True

    # For implicit phrasing, require high semantic confidence to avoid noisy over-filtering.
    return (max(semantic_scores.values()) if semantic_scores else 0.0) >= min_confidence

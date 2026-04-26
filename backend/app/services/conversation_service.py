from __future__ import annotations

import re
from threading import Lock


_context_lock = Lock()
_conversation_context_by_user: dict[int, dict] = {}


def _extract_topic_terms(query: str) -> list[str]:
    tokens = re.findall(r"\b[a-zA-Z]{3,}\b", (query or "").lower())
    stop_words = {
        "what", "when", "where", "who", "did", "does", "about", "show", "tell",
        "me", "my", "the", "and", "for", "this", "that", "those", "these",
        "last", "week", "month", "today", "yesterday", "recent", "summarize",
    }
    filtered = [token for token in tokens if token not in stop_words]
    return filtered[:4]


def _extract_types(memories: list) -> list[str]:
    types = []
    seen = set()
    for memory in memories:
        m_type = getattr(memory, "type", None)
        if not m_type:
            continue
        if m_type in seen:
            continue
        seen.add(m_type)
        types.append(m_type)
    return types


def _is_followup_query(query: str) -> bool:
    q = (query or "").strip().lower()
    followup_markers = [
        "what about",
        "and what",
        "how about",
        "those",
        "that",
        "same",
        "also",
    ]
    if any(marker in q for marker in followup_markers):
        return True

    short_question = len(re.findall(r"\b\w+\b", q)) <= 4 and q.endswith("?")
    return short_question


def normalize_query_with_context(user_id: int, query: str) -> str:
    with _context_lock:
        ctx = _conversation_context_by_user.get(user_id)

    if not ctx:
        return query

    if not _is_followup_query(query):
        return query

    topic_terms = ctx.get("last_topic_terms") or []
    last_types = ctx.get("last_types") or []
    hints = topic_terms + last_types

    if not hints:
        return query

    return f"{query} about {' '.join(hints)}"


def update_context(user_id: int, query: str, memories: list) -> None:
    context_entry = {
        "last_query": query,
        "last_topic_terms": _extract_topic_terms(query),
        "last_types": _extract_types(memories),
        "last_result_ids": [getattr(m, "id", None) for m in memories if getattr(m, "id", None) is not None],
    }
    with _context_lock:
        _conversation_context_by_user[user_id] = context_entry


def get_context(user_id: int) -> dict:
    with _context_lock:
        return dict(_conversation_context_by_user.get(user_id, {}))
from __future__ import annotations

import re
import time
from threading import Lock


_context_lock = Lock()
_conversation_context_by_user: dict[int, dict] = {}
CONTEXT_TTL_SECONDS = 20 * 60
MIN_CONTEXT_CONFIDENCE = 0.35
CONTEXT_MAX_USERS = 2000


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


def _is_context_fresh(ctx: dict, now_ts: float | None = None, ttl_seconds: int = CONTEXT_TTL_SECONDS) -> bool:
    if not ctx:
        return False
    updated_at_ts = float(ctx.get("updated_at_ts") or 0.0)
    if updated_at_ts <= 0.0:
        return False

    current_ts = now_ts if now_ts is not None else time.time()
    return (current_ts - updated_at_ts) <= ttl_seconds


def _context_confidence(ctx: dict) -> float:
    if not ctx:
        return 0.0
    return float(ctx.get("context_confidence") or 0.0)


def _context_gate_decision(query: str, ctx: dict, now_ts: float | None = None) -> tuple[bool, str]:
    if not ctx:
        return False, "no_context"
    if not _is_followup_query(query):
        return False, "not_followup"
    if not _is_context_fresh(ctx=ctx, now_ts=now_ts):
        return False, "context_expired"
    if _context_confidence(ctx) < MIN_CONTEXT_CONFIDENCE:
        return False, "low_confidence"
    return True, "applied"


def _should_apply_context(query: str, ctx: dict, now_ts: float | None = None) -> bool:
    can_apply, _ = _context_gate_decision(query=query, ctx=ctx, now_ts=now_ts)
    return can_apply


def _estimate_context_confidence(query: str, memories: list, time_filters: dict | None = None) -> float:
    topic_terms = _extract_topic_terms(query)
    memory_types = _extract_types(memories)
    result_count = len(memories)
    has_temporal_scope = bool((time_filters or {}).get("start_date") or (time_filters or {}).get("end_date"))

    topic_signal = min(1.0, len(topic_terms) / 4.0)
    type_signal = min(1.0, len(memory_types) / 3.0)
    result_signal = 1.0 if result_count > 0 else 0.0
    temporal_signal = 1.0 if has_temporal_scope else 0.0

    confidence = 0.3 * topic_signal + 0.3 * type_signal + 0.2 * result_signal + 0.2 * temporal_signal
    return round(confidence, 4)


def _prune_stale_contexts(now_ts: float | None = None) -> None:
    current_ts = now_ts if now_ts is not None else time.time()

    # Remove entries older than TTL.
    stale_user_ids = []
    for user_id, ctx in _conversation_context_by_user.items():
        if not _is_context_fresh(ctx=ctx, now_ts=current_ts):
            stale_user_ids.append(user_id)
    for user_id in stale_user_ids:
        _conversation_context_by_user.pop(user_id, None)

    # Hard cap to avoid unbounded memory growth.
    overflow = len(_conversation_context_by_user) - CONTEXT_MAX_USERS
    if overflow > 0:
        oldest = sorted(
            _conversation_context_by_user.items(),
            key=lambda item: float(item[1].get("updated_at_ts") or 0.0),
        )
        for user_id, _ in oldest[:overflow]:
            _conversation_context_by_user.pop(user_id, None)


def merge_time_filters_with_context(user_id: int, query: str, time_filters: dict) -> dict:
    merged = dict(time_filters)

    with _context_lock:
        _prune_stale_contexts()
        ctx = _conversation_context_by_user.get(user_id)

    if not ctx or not _should_apply_context(query=query, ctx=ctx):
        return merged

    last_time_filters = ctx.get("last_time_filters") or {}
    if not last_time_filters:
        return merged

    # In follow-up queries, inherit missing date range from prior context.
    if not merged.get("start_date") and last_time_filters.get("start_date"):
        merged["start_date"] = last_time_filters.get("start_date")
    if not merged.get("end_date") and last_time_filters.get("end_date"):
        merged["end_date"] = last_time_filters.get("end_date")

    return merged


def normalize_query_with_context(user_id: int, query: str) -> str:
    with _context_lock:
        _prune_stale_contexts()
        ctx = _conversation_context_by_user.get(user_id)

    if not ctx:
        return query

    if not _should_apply_context(query=query, ctx=ctx):
        return query

    topic_terms = ctx.get("last_topic_terms") or []
    last_types = ctx.get("last_types") or []
    hints = topic_terms + last_types

    if not hints:
        return query

    return f"{query} about {' '.join(hints)}"


def update_context(
    user_id: int,
    query: str,
    memories: list,
    time_filters: dict | None = None,
    updated_at_ts: float | None = None,
) -> None:
    topic_terms = _extract_topic_terms(query)
    memory_types = _extract_types(memories)

    context_entry = {
        "last_query": query,
        "last_topic_terms": topic_terms,
        "last_types": memory_types,
        "last_result_ids": [getattr(m, "id", None) for m in memories if getattr(m, "id", None) is not None],
        "last_time_filters": dict(time_filters or {}),
        "context_confidence": _estimate_context_confidence(query=query, memories=memories, time_filters=time_filters),
        "updated_at_ts": float(updated_at_ts) if updated_at_ts is not None else time.time(),
    }
    with _context_lock:
        _prune_stale_contexts(now_ts=context_entry["updated_at_ts"])
        _conversation_context_by_user[user_id] = context_entry
        _prune_stale_contexts(now_ts=context_entry["updated_at_ts"])


def get_context(user_id: int) -> dict:
    with _context_lock:
        _prune_stale_contexts()
        return dict(_conversation_context_by_user.get(user_id, {}))


def get_context_observability(user_id: int, query: str, now_ts: float | None = None) -> dict:
    with _context_lock:
        ctx = _conversation_context_by_user.get(user_id)

    can_apply, reason = _context_gate_decision(query=query, ctx=ctx or {}, now_ts=now_ts)
    confidence = _context_confidence(ctx or {})
    is_followup = _is_followup_query(query)
    is_fresh = _is_context_fresh(ctx=ctx or {}, now_ts=now_ts)

    return {
        "applied": can_apply,
        "reason": reason,
        "confidence": round(confidence, 4),
        "is_followup": is_followup,
        "is_fresh": is_fresh,
        "ttl_seconds": CONTEXT_TTL_SECONDS,
        "min_confidence": MIN_CONTEXT_CONFIDENCE,
    }


def reset_context_store() -> None:
    with _context_lock:
        _conversation_context_by_user.clear()
from __future__ import annotations

import re
from datetime import datetime


TYPE_WEIGHTS = {
    "mistake": 1.0,
    "decision": 0.88,
    "goal": 0.84,
    "idea": 0.74,
    "activity": 0.62,
    "event": 0.56,
    "habit": 0.52,
    "emotion": 0.42,
}

KEYWORD_BOOSTS = {
    "important": 0.12,
    "urgent": 0.14,
    "remember": 0.10,
    "deadline": 0.16,
    "meeting": 0.08,
    "project": 0.10,
    "exam": 0.14,
    "interview": 0.15,
    "doctor": 0.12,
    "medicine": 0.12,
    "goal": 0.09,
    "plan": 0.08,
    "mistake": 0.12,
    "error": 0.11,
    "fix": 0.09,
}

HIGH_SIGNAL_PHRASES = {
    "don't forget": 0.16,
    "do not forget": 0.16,
    "must": 0.10,
    "need to": 0.10,
    "should": 0.07,
    "critical": 0.13,
    "priority": 0.14,
}


def _days_since(date_str: str) -> int:
    try:
        parsed = datetime.strptime(date_str, "%Y-%m-%d")
    except (ValueError, TypeError):
        return 999
    return max(0, (datetime.now() - parsed).days)


def _recency_boost(date_str: str) -> float:
    days = _days_since(date_str)
    if days <= 1:
        return 0.18
    if days <= 7:
        return 0.14
    if days <= 30:
        return 0.08
    if days <= 90:
        return 0.04
    return 0.0


def _duration_boost(duration: str | None) -> float:
    if not duration:
        return 0.0
    match = re.search(r"(\d+)", duration)
    if not match:
        return 0.0
    value = int(match.group(1))
    if "min" in duration.lower():
        value = value / 60.0
    if value >= 4:
        return 0.08
    if value >= 2:
        return 0.05
    if value >= 1:
        return 0.03
    return 0.0


def _keyword_boost(text: str) -> float:
    lowered = (text or "").lower()
    boost = 0.0
    for phrase, value in HIGH_SIGNAL_PHRASES.items():
        if phrase in lowered:
            boost += value
    for keyword, value in KEYWORD_BOOSTS.items():
        if re.search(rf"\b{re.escape(keyword)}\b", lowered):
            boost += value
    return boost


def compute_importance_score(memory) -> float:
    memory_type = (getattr(memory, "type", "") or "").lower()
    type_score = TYPE_WEIGHTS.get(memory_type, 0.45)
    recency = _recency_boost(getattr(memory, "date", None))
    duration = _duration_boost(getattr(memory, "duration", None))
    keyword = _keyword_boost(getattr(memory, "content", "") or "")

    score = type_score + recency + duration + keyword
    return round(max(0.0, min(score, 1.0)), 4)


def explain_importance(memory) -> list[str]:
    reasons = []
    memory_type = (getattr(memory, "type", "") or "").lower()
    if memory_type in TYPE_WEIGHTS:
        reasons.append(f"type:{memory_type}")

    if _days_since(getattr(memory, "date", None)) <= 7:
        reasons.append("recent")

    if getattr(memory, "duration", None):
        reasons.append("duration")

    text = (getattr(memory, "content", "") or "").lower()
    for signal in ["important", "urgent", "deadline", "remember", "critical", "priority"]:
        if signal in text:
            reasons.append(signal)

    return reasons[:4]
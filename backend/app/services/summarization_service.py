from collections import Counter
import re
from datetime import datetime, timedelta

from app.services.importance_service import compute_importance_score
from app.services.temporal_service import parse_query_time_filters


SUMMARY_STOPWORDS = {
    "today",
    "yesterday",
    "studied",
    "worked",
    "about",
    "with",
    "this",
    "that",
    "from",
    "into",
    "have",
    "been",
    "were",
    "was",
    "just",
    "more",
    "most",
}

IMPORTANT_THRESHOLD = 0.7


def _extract_tokens(text: str) -> list[str]:
    return [
        token
        for token in re.findall(r"\b[a-zA-Z]{3,}\b", (text or "").lower())
        if token not in SUMMARY_STOPWORDS
    ]


def _format_highlights(highlights: list[str]) -> str:
    if not highlights:
        return "none"
    return "; ".join(highlights)


def _shorten(text: str, limit: int = 90) -> str:
    cleaned = (text or "").strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1].rstrip() + "…"


def summarize_memories(memories):
    if not memories:
        return "No memories found for this period."

    total_hours = 0
    types = []
    themes = Counter()
    priority_themes = Counter()
    important_highlights = []

    for m in memories:
        importance = compute_importance_score(m)

        if m.duration:
            try:
                value = int(re.search(r"(\d+)", m.duration).group(1))
                if "min" in m.duration.lower():
                    total_hours += value / 60
                else:
                    total_hours += value
            except (AttributeError, ValueError, TypeError):
                pass

        types.append(m.type)

        tokens = _extract_tokens(m.content)
        for token in tokens:
            themes[token] += 1
            if importance >= IMPORTANT_THRESHOLD:
                priority_themes[token] += 1

        if importance >= IMPORTANT_THRESHOLD:
            important_highlights.append((importance, _shorten(m.content)))

    type_counter = Counter(types)
    most_common_type = type_counter.most_common(1)[0][0]
    top_themes = [w for w, _ in themes.most_common(3)]
    top_priority_themes = [w for w, _ in priority_themes.most_common(3)]
    themes_text = ", ".join(top_themes) if top_themes else "general tasks"
    priority_themes_text = ", ".join(top_priority_themes) if top_priority_themes else "no priority-specific themes"
    priority_count = len(important_highlights)
    sorted_highlights = [
        highlight
        for _, highlight in sorted(important_highlights, key=lambda item: item[0], reverse=True)[:3]
        if highlight
    ]

    return (
        f"You mainly focused on {most_common_type} memories.\n"
        f"You logged {len(memories)} memories in total.\n"
        f"Estimated tracked time: {round(total_hours, 2)} hours.\n"
        f"Top themes: {themes_text}.\n"
        f"Priority memories: {priority_count}.\n"
        f"Priority themes: {priority_themes_text}.\n"
        f"Key highlights: {_format_highlights(sorted_highlights)}."
    )


def get_date_range(period: str):
    filters = parse_query_time_filters(period, now=datetime.now())
    start = filters.get("start_date")
    end = filters.get("end_date")
    if start and end:
        return start, end

    now = datetime.now()
    start = now - timedelta(days=7)
    return start.strftime("%Y-%m-%d"), now.strftime("%Y-%m-%d")
from collections import Counter
import re
from datetime import datetime, timedelta
from app.services.temporal_service import parse_query_time_filters


def summarize_memories(memories):
    if not memories:
        return "No memories found for this period."

    total_hours = 0
    types = []
    themes = Counter()

    for m in memories:
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

        for token in re.findall(r"\b[a-zA-Z]{3,}\b", m.content.lower()):
            if token not in {"today", "yesterday", "studied", "worked", "about", "with"}:
                themes[token] += 1

    type_counter = Counter(types)
    most_common_type = type_counter.most_common(1)[0][0]
    top_themes = [w for w, _ in themes.most_common(3)]
    themes_text = ", ".join(top_themes) if top_themes else "general tasks"

    return (
        f"You mainly focused on {most_common_type} memories.\n"
        f"You logged {len(memories)} memories in total.\n"
        f"Estimated tracked time: {round(total_hours, 2)} hours.\n"
        f"Top themes: {themes_text}."
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
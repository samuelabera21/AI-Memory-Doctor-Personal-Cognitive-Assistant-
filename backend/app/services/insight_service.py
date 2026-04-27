from collections import Counter
import re
from datetime import datetime

from app.services.importance_service import compute_importance_score


IMPORTANT_THRESHOLD = 0.7


def _shorten(text: str, limit: int = 72) -> str:
    cleaned = (text or "").strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1].rstrip() + "…"


def extract_hour(time_str):
    try:
        return int(time_str.split(":")[0])
    except:
        return None


def get_time_bucket(hour):
    if hour is None:
        return "unknown"
    if 5 <= hour < 12:
        return "morning"
    elif 12 <= hour < 17:
        return "afternoon"
    elif 17 <= hour < 22:
        return "evening"
    return "night"


def analyze_insights(memories):
    if not memories:
        return {
            "status": "insufficient_data",
            "insight": "No data to analyze.",
            "most_common_type": None,
            "most_productive_time": None,
            "repeated_mistakes": [],
            "trend": "no_data",
            "priority_count": 0,
            "priority_ratio": 0.0,
            "priority_focus": None,
            "priority_highlights": [],
        }

    if len(memories) < 3:
        return {
            "status": "insufficient_data",
            "insight": "More memories are needed for reliable pattern insights. Add at least 3 memories across different times/days.",
            "most_common_type": memories[0].type if memories else None,
            "most_productive_time": None,
            "repeated_mistakes": [],
            "trend": "insufficient_data",
            "priority_count": 0,
            "priority_ratio": 0.0,
            "priority_focus": None,
            "priority_highlights": [],
        }

    types = []
    time_buckets = []
    durations = {}
    mistake_keywords = Counter()
    by_date = Counter()
    priority_counter = Counter()
    priority_highlights = []
    priority_count = 0

    for m in memories:
        types.append(m.type)
        by_date[m.date] += 1

        importance = compute_importance_score(m)
        if importance >= IMPORTANT_THRESHOLD:
            priority_count += 1
            priority_counter[(m.type or "unknown").lower()] += 1
            priority_highlights.append(_shorten(m.content))

        hour = extract_hour(m.time)
        bucket = get_time_bucket(hour)
        time_buckets.append(bucket)

        if m.duration:
            match = re.search(r'\d+', m.duration)
            if match:
                val = int(match.group())
                durations[m.type] = durations.get(m.type, 0) + val

        if (m.type or "") == "mistake":
            for token in re.findall(r"\b[a-zA-Z]{3,}\b", (m.content or "").lower()):
                if token not in {"mistake", "again", "same"}:
                    mistake_keywords[token] += 1

    most_common_type = Counter(types).most_common(1)[0][0]
    best_time = Counter(time_buckets).most_common(1)[0][0]

    if durations:
        max_type = max(durations, key=durations.get)
    else:
        max_type = most_common_type

    dates_sorted = sorted(by_date.keys())
    trend = "stable"
    if len(dates_sorted) >= 2:
        first_half = sum(by_date[d] for d in dates_sorted[: len(dates_sorted) // 2 or 1])
        second_half = sum(by_date[d] for d in dates_sorted[len(dates_sorted) // 2 :])
        if second_half > first_half:
            trend = "increasing"
        elif second_half < first_half:
            trend = "decreasing"

    repeated_mistakes = [w for w, _ in mistake_keywords.most_common(3)]
    priority_ratio = round(priority_count / len(memories), 4)
    priority_focus = priority_counter.most_common(1)[0][0] if priority_counter else None
    priority_highlights = [item for item in priority_highlights[:3] if item]

    narrative = (
        f"Your most frequent memory type is '{most_common_type}'. "
        f"You are most active during the {best_time}. "
        f"You spend the most time on '{max_type}'."
    )
    if priority_count:
        narrative += (
            f" High-priority memories make up {round(priority_ratio * 100)}% of your log"
            f" and are concentrated in '{priority_focus}'."
        )
        if priority_highlights:
            narrative += f" Key priority examples: {', '.join(priority_highlights)}."
    if repeated_mistakes:
        narrative += f" Repeated mistake themes: {', '.join(repeated_mistakes)}."

    return {
        "status": "ready",
        "insight": narrative,
        "most_common_type": most_common_type,
        "most_productive_time": best_time,
        "repeated_mistakes": repeated_mistakes,
        "trend": trend,
        "priority_count": priority_count,
        "priority_ratio": priority_ratio,
        "priority_focus": priority_focus,
        "priority_highlights": priority_highlights,
    }
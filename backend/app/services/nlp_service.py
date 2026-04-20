from datetime import datetime
import re
from dateutil import parser
from app.services.ml_classifier_service import predict_memory_type
from zoneinfo import ZoneInfo
from app.config import settings

_STOPWORDS = {
    "i", "for", "the", "a", "an", "and", "to", "of", "in", "on", "at", "is", "was", "were", "my", "me"
}


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def classify_type(text: str):
    return predict_memory_type(text)


def extract_tags(text: str):
    words = re.findall(r"\b[a-zA-Z][a-zA-Z\-]{1,}\b", text.lower())
    clean_words = [w for w in words if w not in _STOPWORDS]
    seen = set()
    tags = []
    for word in clean_words:
        if word not in seen:
            tags.append(word)
            seen.add(word)
        if len(tags) >= 8:
            break
    return tags


def extract_duration(text: str):
    match = re.search(r"(\d+)\s*(hours?|hrs?|minutes?|mins?)", text.lower())
    if not match:
        return None
    return f"{match.group(1)} {match.group(2)}"


def extract_datetime_from_text(text: str, now: datetime | None = None):
    tz = ZoneInfo(settings.timezone)
    now = now or datetime.now(tz)
    lowered = text.lower()

    explicit_time_match = re.search(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b", lowered)

    parse_text = re.sub(r"\b(I|AI)\b", "", text, flags=re.IGNORECASE)

    try:
        parsed = parser.parse(parse_text, fuzzy=True, default=now)
    except (ValueError, TypeError, OverflowError):
        parsed = now

    if explicit_time_match:
        hour = int(explicit_time_match.group(1)) % 12
        minute = int(explicit_time_match.group(2) or "0")
        meridiem = explicit_time_match.group(3)
        if meridiem == "pm":
            hour += 12
        parsed = parsed.replace(hour=hour, minute=minute)

    if "yesterday" in lowered:
        parsed = parsed.replace(year=now.year, month=now.month, day=now.day)
        parsed = parsed.fromordinal(parsed.toordinal() - 1)
    elif "today" in lowered:
        parsed = parsed.replace(year=now.year, month=now.month, day=now.day)

    if "morning" in lowered and not explicit_time_match:
        parsed = parsed.replace(hour=9, minute=0)
    elif "afternoon" in lowered and not explicit_time_match:
        parsed = parsed.replace(hour=14, minute=0)
    elif any(token in lowered for token in ["evening", "night"]) and not explicit_time_match:
        parsed = parsed.replace(hour=19, minute=0)

    return {
        "date": parsed.strftime("%Y-%m-%d"),
        "time": parsed.strftime("%H:%M"),
    }


def structure_memory_text(text: str, fallback_time: str | None = None):
    normalized = normalize_text(text)
    dt = extract_datetime_from_text(normalized)

    if fallback_time:
        dt["time"] = fallback_time

    return {
        "date": dt["date"],
        "time": dt["time"],
        "type": classify_type(normalized),
        "content": normalized,
        "duration": extract_duration(normalized),
        "tags": extract_tags(normalized),
        "source_text": text,
    }
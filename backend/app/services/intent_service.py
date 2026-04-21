def detect_intent(text: str) -> str:
    text = (text or "").strip().lower()

    if not text:
        return "unknown"

    if any(word in text for word in [
        "summarize", "summary", "summarization", "this week", "this month", "today summary",
        "weekly review", "monthly review", "review my",
    ]):
        return "summarize"

    if any(word in text for word in ["insight", "pattern", "most common", "productive", "repeat"]):
        return "insight"

    if any(word in text for word in ["actually", "not", "update", "correct", "edit"]):
        return "update"

    if text.endswith("?") or any(word in text for word in [
        "what", "when", "where", "did i", "do i", "show", "find", "recall", "last", "search"
    ]):
        return "search"

    if any(word in text for word in ["i ", "today", "learned", "studied", "worked", "decided", "attended"]):
        return "store"

    if "remind" in text:
        return "reminder"

    return "unknown"
from app.services.llm_service import generate_grounded_answer


def _with_duration(content: str, duration: str | None) -> str:
    if duration:
        return f"{content} (duration: {duration})"
    return content


def _human_type(memory_type: str | None) -> str:
    if not memory_type:
        return "memory"
    mapping = {
        "activity": "activity",
        "goal": "goal",
        "decision": "decision",
        "habit": "habit",
        "mistake": "mistake",
        "event": "event",
        "idea": "idea",
        "emotion": "emotion",
    }
    return mapping.get(memory_type, memory_type)


def _friendly_fallback_answer(query: str, memories: list) -> str:
    q = query.lower()
    by_time = sorted(memories, key=lambda m: (m.date or "", m.time or ""))

    if len(by_time) == 1:
        m = by_time[0]
        detail = _with_duration(m.content, m.duration)
        return (
            f"You have 1 matching {_human_type(m.type)}. "
            f"On {m.date} at {m.time}, you {detail}."
        )

    dates = sorted({m.date for m in by_time if m.date})
    same_day = len(dates) == 1
    day_label = "today" if "today" in q else (dates[0] if same_day and dates else "the selected period")

    lines = []
    for m in by_time[:6]:
        detail = _with_duration(m.content, m.duration)
        lines.append(f"- {m.time} | {_human_type(m.type)}: {detail}")

    opener = (
        f"Here is your personal memory recap for {day_label}. "
        f"You logged {len(by_time)} relevant memories."
    )

    if "what did i" in q or "did i" in q or "today" in q:
        opener = (
            f"You did {len(by_time)} notable things in {day_label}. "
            "Here is a clear timeline:"
        )

    return f"{opener}\n" + "\n".join(lines)


def generate_answer(query: str, memories: list):
    if not memories:
        q = query.lower()
        if "mistake" in q:
            return "No mistakes found."
        if "habit" in q:
            return "No habits recorded."
        if "event" in q:
            return "No events found."
        return "I couldn't find anything related."

    memory_rows = [
        {
            "id": m.id,
            "date": m.date,
            "time": m.time,
            "type": m.type,
            "content": m.content,
            "duration": m.duration,
        }
        for m in memories
    ]

    llm_answer = generate_grounded_answer(query=query, memory_rows=memory_rows)
    if llm_answer:
        return llm_answer

    q = query.lower()

    if "last" in q and ("when" in q or "did i" in q):
        latest = sorted(memories, key=lambda m: (m.date or "", m.time or ""), reverse=True)[0]
        duration_part = f" for {latest.duration}" if latest.duration else ""
        return f"Your latest related memory was on {latest.date} at {latest.time}: {latest.content}{duration_part}."

    return _friendly_fallback_answer(query=query, memories=memories)
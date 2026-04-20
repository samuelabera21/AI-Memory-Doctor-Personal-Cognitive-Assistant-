from app.services.llm_service import generate_grounded_answer


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

    answers = ["Here are the most relevant memories:"]

    for m in memories:
        sentence = f"- {m.date} {m.time} | {m.type}: {m.content}"
        if m.duration:
            sentence += f" (duration: {m.duration})"

        answers.append(sentence)

    return "\n".join(answers)
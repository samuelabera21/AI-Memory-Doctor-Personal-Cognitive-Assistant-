# simple in-memory session (per user later)
conversation_context = {
    "last_topic": None,
    "last_results": []
}


def update_context(query: str, memories: list):
    query = query.lower()

    # detect topic
    if "study" in query or "learn" in query:
        conversation_context["last_topic"] = "study"
    elif "work" in query:
        conversation_context["last_topic"] = "work"

    conversation_context["last_results"] = memories


def get_context():
    return conversation_context
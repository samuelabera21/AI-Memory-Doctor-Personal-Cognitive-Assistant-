from app.config import settings
import json
import logging

logger = logging.getLogger(__name__)


def _gemini_generate(query: str, memory_rows: list[dict]) -> str | None:
    try:
        import google.generativeai as genai
    except ImportError:
        return None

    if not settings.llm_api_key:
        return None

    try:
        genai.configure(api_key=settings.llm_api_key)
        model = genai.GenerativeModel(settings.llm_model)

        prompt = (
            "You are AI Memory Doctor. Answer only from retrieved memories. "
            "If not enough evidence, say you could not find it. "
            "Keep answer concise, friendly, and in English. "
            "Use user-centric wording like 'You did...' and prefer a clear timeline when relevant.\n\n"
            f"Query: {query}\n"
            f"Memories: {json.dumps(memory_rows, ensure_ascii=True)}"
        )

        response = model.generate_content(prompt)
        text = getattr(response, "text", None)
        if text:
            return text.strip()
    except Exception as exc:
        logger.warning("Gemini generation failed: %s", exc)
        return None
    return None


def generate_grounded_answer(query: str, memory_rows: list[dict]) -> str | None:
    """
    Placeholder for external LLM call.
    Returns None when LLM is not configured so caller can use deterministic fallback.
    """
    if settings.llm_provider == "none" or not settings.llm_api_key:
        return None

    if settings.llm_provider.lower() == "gemini":
        return _gemini_generate(query=query, memory_rows=memory_rows)

    return None

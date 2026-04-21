from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.services.intent_service import detect_intent

from app.api.memory import MemoryInput, add_memory
from app.api.search import SearchInput, search_memory

from app.services.dependency import get_current_user

from app.api.summarization import summarize, SummaryInput

from app.api.insight import get_insights

from app.api.memory_manage import correction_update, CorrectionInput

router = APIRouter()


class UserInput(BaseModel):
    text: str


@router.post("/agent")
def agent_handler(data: UserInput, user=Depends(get_current_user)):
    user_text = data.text

    intent = detect_intent(user_text)

    def with_intent(payload):
        if isinstance(payload, dict):
            return {"intent": intent, **payload}
        return {"intent": intent, "data": payload}

    if intent == "store":
        return with_intent(add_memory(MemoryInput(content=user_text), user=user))

    if intent == "search":
        return with_intent(search_memory(SearchInput(query=user_text), user=user))

    if intent == "reminder":
        return with_intent({"message": "Reminder feature coming soon"})

    if intent == "summarize":
        return with_intent(summarize(SummaryInput(query=user_text), user=user))

    if intent == "insight":
        return with_intent(get_insights(user=user))

    if intent == "update":
        return with_intent(correction_update(CorrectionInput(text=user_text), user=user))

    return with_intent({
        "message": "I didn't understand",
        "hint": "Try storing a memory, asking a query, requesting summary, or sending a correction."
    })
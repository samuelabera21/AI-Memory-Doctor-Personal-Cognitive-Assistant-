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

    if intent == "store":
        return add_memory(MemoryInput(content=user_text), user=user)

    if intent == "search":
        return search_memory(SearchInput(query=user_text), user=user)

    if intent == "reminder":
        return {"message": "Reminder feature coming soon"}

    if intent == "summarize":
        return summarize(SummaryInput(query=user_text), user=user)

    if intent == "insight":
        return get_insights(user=user)

    if intent == "update":
        return correction_update(CorrectionInput(text=user_text), user=user)

    return {
        "message": "I didn't understand",
        "hint": "Try storing a memory, asking a query, requesting summary, or sending a correction."
    }
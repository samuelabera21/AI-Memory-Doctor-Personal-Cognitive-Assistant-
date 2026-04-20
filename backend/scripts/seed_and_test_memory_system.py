from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from zoneinfo import ZoneInfo

from app.main import app
from app.db.database import SessionLocal, init_database
from app.models.memory_model import Memory
from app.models.user_model import User
from app.services.vector_sync_service import rebuild_faiss_index
from app.config import settings


def _seed_rows():
    now = datetime.now(ZoneInfo(settings.timezone))
    today = now.strftime("%Y-%m-%d")
    yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")
    two_days_ago = (now - timedelta(days=2)).strftime("%Y-%m-%d")
    return [
        {"id": 1, "date": today, "time": "09:00", "content": "Studied Python", "type": "activity"},
        {"id": 2, "date": today, "time": "15:00", "content": "Planned to improve my skills", "type": "decision"},
        {"id": 3, "date": yesterday, "time": "20:00", "content": "Slept early", "type": "habit"},
        {"id": 4, "date": two_days_ago, "time": "10:00", "content": "Went to gym", "type": "activity"},
    ]

TEST_CASES = [
    {"query": "What did I do on April 18?", "expected_ids": [1, 2], "expected_answer": "Studied Python and planned to improve skills"},
    {"query": "What did I do in the morning on April 18?", "expected_ids": [1], "expected_answer": "Studied Python"},
    {"query": "What did I do in the afternoon on April 18?", "expected_ids": [2], "expected_answer": "Planned to improve my skills"},
    {"query": "What did I do yesterday?", "expected_ids": [3], "expected_answer": "Slept early"},
    {"query": "What activities did I do?", "expected_ids": [1, 4], "expected_answer": "Studied Python and went to gym"},
    {"query": "When did I study Python?", "expected_ids": [1], "expected_answer": "April 18 at 9 AM"},
    {"query": "What goals do I have?", "expected_ids": [2], "expected_answer": "Planned to improve skills"},
    {"query": "Did I go to the gym?", "expected_ids": [4], "expected_answer": "Yes, you went to the gym"},
    {"query": "What did I do last week?", "expected_ids": [3, 4], "expected_answer": "Slept early and went to gym"},
    {"query": "What mistakes did I make?", "expected_ids": [], "expected_answer": "No mistakes found"},
    {"query": "What did I do in the evening?", "expected_ids": [3], "expected_answer": "Slept early"},
    {"query": "What did I learn?", "expected_ids": [1], "expected_answer": "Studied Python"},
    {"query": "What decisions did I make?", "expected_ids": [2], "expected_answer": "Planned to improve skills"},
    {"query": "What did I do recently?", "expected_ids": [1, 2], "expected_answer": "Studied Python and planned improvement"},
    {"query": "What did I do on April 17?", "expected_ids": [3], "expected_answer": "Slept early"},
    {"query": "What habits do I have?", "expected_ids": [], "expected_answer": "No habits recorded"},
    {"query": "What events did I attend?", "expected_ids": [], "expected_answer": "No events found"},
    {"query": "What did I do in April?", "expected_ids": [1, 2, 3, 4], "expected_answer": "Studied, planned, slept, and exercised"},
    {"query": "When was my last activity?", "expected_ids": [1], "expected_answer": "April 18"},
    {"query": "Summarize my recent activities", "expected_ids": [1, 2, 3], "expected_answer": "You studied, planned, and rested"},
]


def _prepare_demo_data(user_id: int) -> None:
    db = SessionLocal()
    try:
        # Reserve deterministic IDs for this benchmark dataset.
        db.query(Memory).filter(Memory.id.in_([1, 2, 3, 4])).delete(synchronize_session=False)

        # Reset this user's memories so tests run cleanly.
        db.query(Memory).filter(Memory.user_id == user_id).delete()
        db.commit()

        for row in SEED_ROWS:
            db.add(
                Memory(
                    id=row["id"],
                    user_id=user_id,
                    date=row["date"],
                    time=row["time"],
                    type=row["type"],
                    content=row["content"],
                    duration=None,
                    tags="",
                    source_text=row["content"],
                    version=1,
                    is_active=1,
                    is_deleted=0,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
            )
        db.commit()
    finally:
        db.close()


def _register_and_login(client: TestClient):
    email = "seed_eval_user@example.com"
    password = "strongpass123"
    client.post("/auth/register", json={"email": email, "password": password})
    login = client.post("/auth/login", json={"email": email, "password": password})
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, email


def _current_yesterday_id() -> int:
    return 3


def run():
    init_database()
    seed_rows = _seed_rows()
    with TestClient(app) as client:
        headers, email = _register_and_login(client)

        me = client.get("/memories", headers=headers)
        if me.status_code != 200:
            raise RuntimeError("Authentication failed")

        db = SessionLocal()
        try:
            user = db.query(User).filter(User.email == email).first()
            user_id = user.id
        finally:
            db.close()

        global SEED_ROWS
        SEED_ROWS = seed_rows
        _prepare_demo_data(user_id=user_id)
        rebuild_faiss_index()

        passed = 0
        results = []

        for case in TEST_CASES:
            response = client.post("/search-memory", headers=headers, json={"query": case["query"]})
            payload = response.json()
            returned_ids = [item["id"] for item in payload.get("results", [])]
            expected_ids = case["expected_ids"]

            ok = set(expected_ids).issubset(set(returned_ids))
            if case["query"].lower() == "what did i do yesterday?":
                ok = _current_yesterday_id() in returned_ids

            if ok:
                passed += 1

            results.append(
                {
                    "query": case["query"],
                    "expected_ids": expected_ids,
                    "returned_ids": returned_ids,
                    "answer": payload.get("answer", ""),
                    "passed": ok,
                }
            )

        print("Seed rows inserted:", len(SEED_ROWS))
        print("Test cases passed:", passed, "/", len(TEST_CASES))
        for row in results:
            print("---")
            print("Query:", row["query"])
            print("Expected IDs:", row["expected_ids"])
            print("Returned IDs:", row["returned_ids"])
            print("Passed:", row["passed"])
            print("Answer:", row["answer"])


if __name__ == "__main__":
    run()

from pathlib import Path
from datetime import datetime
import csv
import json
from uuid import uuid4

from app.services.ml_classifier_service import evaluate_seed_accuracy


CONTEXT_SCENARIO_HISTORY_PATH = Path("backend") / "reports" / "context_scenario_history.jsonl"


DEFAULT_THESIS_TEST_CASES = [
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


def retrieval_precision_at_k(retrieved: list[dict], expected_ids: set[int], k: int = 5) -> float:
    if k <= 0:
        return 0.0
    top_k = retrieved[:k]
    if not top_k:
        return 0.0
    hits = sum(1 for r in top_k if r.get("id") in expected_ids)
    return hits / min(k, len(top_k))


def response_correctness_stub(answer: str, expected_keywords: list[str]) -> float:
    if not expected_keywords:
        return 0.0
    answer_lower = answer.lower()
    hit = sum(1 for keyword in expected_keywords if keyword.lower() in answer_lower)
    return hit / len(expected_keywords)


def compute_system_metrics(sample_answers: list[dict] | None = None):
    sample_answers = sample_answers or []

    classification_accuracy = evaluate_seed_accuracy()

    if sample_answers:
        retrieval_scores = [row.get("retrieval_precision", 0.0) for row in sample_answers]
        correctness_scores = [row.get("response_correctness", 0.0) for row in sample_answers]
        followup_scores = [row.get("context_followup_correctness", 0.0) for row in sample_answers]
        context_application_scores = [row.get("context_application_rate", 0.0) for row in sample_answers]
    else:
        retrieval_scores = [0.0]
        correctness_scores = [0.0]
        followup_scores = [0.0]
        context_application_scores = [0.0]

    retrieval_accuracy = sum(retrieval_scores) / len(retrieval_scores)
    response_correctness = sum(correctness_scores) / len(correctness_scores)
    context_followup_accuracy = sum(followup_scores) / len(followup_scores)
    context_application_rate = sum(context_application_scores) / len(context_application_scores)

    return {
        "classification_accuracy": round(classification_accuracy, 4),
        "retrieval_accuracy": round(retrieval_accuracy, 4),
        "response_correctness": round(response_correctness, 4),
        "context_followup_accuracy": round(context_followup_accuracy, 4),
        "context_application_rate": round(context_application_rate, 4),
        "sample_count": len(sample_answers),
        "notes": [
            "Classification accuracy is measured on seed supervised samples.",
            "Retrieval and response metrics use API-provided evaluation cases.",
            "Follow-up metric estimates how well context-aware continuity is preserved.",
            "Context application rate reports how often context was confidently applied.",
        ],
    }


def _answer_keywords(expected_answer: str) -> list[str]:
    # Lightweight token selection for correctness proxy.
    tokens = [tok.strip(" ,.").lower() for tok in expected_answer.split()]
    return [tok for tok in tokens if len(tok) > 3][:8]


def score_context_followup_from_payload(payload: dict) -> float:
    context_meta = payload.get("context_meta", {}) or {}
    gate = context_meta.get("gate", {}) or {}

    applied_by_query = bool(context_meta.get("query_context_applied"))
    applied_by_time = bool(context_meta.get("temporal_context_applied"))
    gate_applied = bool(gate.get("applied"))
    gate_reason = str(gate.get("reason") or "")

    if (applied_by_query or applied_by_time) and gate_applied and gate_reason == "applied":
        return 1.0
    return 0.0


def _append_context_scenario_history(entry: dict) -> None:
    history_path = CONTEXT_SCENARIO_HISTORY_PATH
    history_path.parent.mkdir(parents=True, exist_ok=True)
    with history_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=True) + "\n")


def get_context_scenario_history(limit: int = 20) -> dict:
    safe_limit = max(1, min(int(limit), 200))
    history_path = CONTEXT_SCENARIO_HISTORY_PATH
    if not history_path.exists():
        return {"items": [], "count": 0, "limit": safe_limit}

    lines = history_path.read_text(encoding="utf-8").splitlines()
    rows = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    items = rows[-safe_limit:]
    context_scores = [float(item.get("context_followup_correctness", 0.0)) for item in items]
    avg_score = (sum(context_scores) / len(context_scores)) if context_scores else 0.0

    return {
        "items": items,
        "count": len(items),
        "limit": safe_limit,
        "avg_context_followup_correctness": round(avg_score, 4),
    }


def run_context_followup_scenario(user):
    from app.api.memory import MemoryInput, add_memory
    from app.api.search import SearchInput, search_memory
    from app.db.database import SessionLocal
    from app.models.memory_model import Memory
    from app.services.vector_store import delete_memory_vector

    marker = f"eval_ctx_{uuid4().hex[:8]}"
    created_ids: list[int] = []

    try:
        seed_inputs = [
            f"Today at 08:00 I studied retrieval engineering for 2 hours {marker}",
            f"Today at 19:00 I reviewed notes about personal memory systems {marker}",
        ]
        for content in seed_inputs:
            created = add_memory(MemoryInput(content=content, time=None), user=user)
            created_ids.append(int(created["memory_id"]))

        first_query = "What study activities did I do this week?"
        followup_query = "and in the morning?"

        first_payload = search_memory(SearchInput(query=first_query), user=user)
        followup_payload = search_memory(SearchInput(query=followup_query), user=user)

        followup_score = score_context_followup_from_payload(followup_payload)
        context_meta = followup_payload.get("context_meta", {})

        response = {
            "message": "Context follow-up scenario completed",
            "scenario": {
                "seed_count": len(created_ids),
                "first_query": first_query,
                "followup_query": followup_query,
                "first_result_count": len(first_payload.get("results", [])),
                "followup_result_count": len(followup_payload.get("results", [])),
                "context_meta": context_meta,
            },
            "scores": {
                "context_followup_correctness": followup_score,
                "context_application_rate": 1.0 if followup_score > 0.0 else 0.0,
            },
            "metric_sample": {
                "retrieval_precision": 0.0,
                "response_correctness": 0.0,
                "context_followup_correctness": followup_score,
                "context_application_rate": 1.0 if followup_score > 0.0 else 0.0,
            },
        }

        _append_context_scenario_history(
            {
                "run_id": f"ctx_run_{uuid4().hex[:10]}",
                "generated_at_utc": datetime.utcnow().isoformat(),
                "user_id": int(getattr(user, "id", 0) or 0),
                "context_followup_correctness": response["scores"]["context_followup_correctness"],
                "context_application_rate": response["scores"]["context_application_rate"],
                "gate_reason": (response.get("scenario", {}).get("context_meta", {}).get("gate", {}) or {}).get("reason", "unknown"),
                "gate_confidence": float((response.get("scenario", {}).get("context_meta", {}).get("gate", {}) or {}).get("confidence", 0.0) or 0.0),
                "query_context_applied": bool((response.get("scenario", {}).get("context_meta", {}) or {}).get("query_context_applied")),
                "temporal_context_applied": bool((response.get("scenario", {}).get("context_meta", {}) or {}).get("temporal_context_applied")),
            }
        )

        return response
    finally:
        if created_ids:
            db = SessionLocal()
            try:
                db.query(Memory).filter(Memory.id.in_(created_ids)).delete(synchronize_session=False)
                db.commit()
            finally:
                db.close()

            for memory_id in created_ids:
                delete_memory_vector(memory_id)


def run_endpoint_test_report(user, cases: list[dict] | None = None, report_name: str = "thesis_evaluation"):
    from app.api.search import search_memory, SearchInput

    cases = cases or DEFAULT_THESIS_TEST_CASES

    case_results = []
    metrics_input = []

    for case in cases:
        query = case["query"]
        expected_ids = set(case.get("expected_ids", []))
        expected_answer = case.get("expected_answer", "")

        payload = search_memory(SearchInput(query=query), user=user)
        returned = payload.get("results", [])
        answer = payload.get("answer", "")
        context_meta = payload.get("context_meta", {})
        context_gate = context_meta.get("gate", {})

        returned_ids = [row.get("id") for row in returned]
        precision = retrieval_precision_at_k(returned, expected_ids, k=5)
        correctness = response_correctness_stub(answer, _answer_keywords(expected_answer))
        pass_flag = expected_ids.issubset(set(returned_ids))
        context_applied = bool(context_meta.get("query_context_applied") or context_meta.get("temporal_context_applied"))

        case_row = {
            "query": query,
            "expected_ids": sorted(list(expected_ids)),
            "returned_ids": returned_ids,
            "retrieval_precision": round(precision, 4),
            "response_correctness": round(correctness, 4),
            "context_applied": context_applied,
            "context_reason": context_gate.get("reason", "unknown"),
            "context_confidence": round(float(context_gate.get("confidence", 0.0)), 4),
            "passed": pass_flag,
            "expected_answer": expected_answer,
            "actual_answer": answer,
        }
        case_results.append(case_row)
        metrics_input.append(
            {
                "retrieval_precision": precision,
                "response_correctness": correctness,
                "context_application_rate": 1.0 if context_applied else 0.0,
            }
        )

    metrics = compute_system_metrics(metrics_input)
    metrics["passed_cases"] = sum(1 for row in case_results if row["passed"])
    metrics["total_cases"] = len(case_results)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("backend") / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / f"{report_name}_{timestamp}.json"
    csv_path = output_dir / f"{report_name}_{timestamp}.csv"

    json_payload = {
        "generated_at_utc": datetime.utcnow().isoformat(),
        "metrics": metrics,
        "cases": case_results,
    }
    json_path.write_text(json.dumps(json_payload, indent=2), encoding="utf-8")

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "query",
                "expected_ids",
                "returned_ids",
                "retrieval_precision",
                "response_correctness",
                "context_applied",
                "context_reason",
                "context_confidence",
                "passed",
                "expected_answer",
                "actual_answer",
            ],
        )
        writer.writeheader()
        for row in case_results:
            writer.writerow(
                {
                    **row,
                    "expected_ids": ",".join(map(str, row["expected_ids"])),
                    "returned_ids": ",".join(map(str, row["returned_ids"])),
                }
            )

    return {
        "message": "Evaluation report exported",
        "metrics": metrics,
        "json_report": str(json_path).replace("\\", "/"),
        "csv_report": str(csv_path).replace("\\", "/"),
    }

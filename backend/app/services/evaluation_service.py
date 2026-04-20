from pathlib import Path
from datetime import datetime
import csv
import json

from app.services.ml_classifier_service import evaluate_seed_accuracy
from app.api.search import search_memory, SearchInput


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
    else:
        retrieval_scores = [0.0]
        correctness_scores = [0.0]

    retrieval_accuracy = sum(retrieval_scores) / len(retrieval_scores)
    response_correctness = sum(correctness_scores) / len(correctness_scores)

    return {
        "classification_accuracy": round(classification_accuracy, 4),
        "retrieval_accuracy": round(retrieval_accuracy, 4),
        "response_correctness": round(response_correctness, 4),
        "sample_count": len(sample_answers),
        "notes": [
            "Classification accuracy is measured on seed supervised samples.",
            "Retrieval and response metrics use API-provided evaluation cases.",
        ],
    }


def _answer_keywords(expected_answer: str) -> list[str]:
    # Lightweight token selection for correctness proxy.
    tokens = [tok.strip(" ,.").lower() for tok in expected_answer.split()]
    return [tok for tok in tokens if len(tok) > 3][:8]


def run_endpoint_test_report(user, cases: list[dict] | None = None, report_name: str = "thesis_evaluation"):
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

        returned_ids = [row.get("id") for row in returned]
        precision = retrieval_precision_at_k(returned, expected_ids, k=5)
        correctness = response_correctness_stub(answer, _answer_keywords(expected_answer))
        pass_flag = expected_ids.issubset(set(returned_ids))

        case_row = {
            "query": query,
            "expected_ids": sorted(list(expected_ids)),
            "returned_ids": returned_ids,
            "retrieval_precision": round(precision, 4),
            "response_correctness": round(correctness, 4),
            "passed": pass_flag,
            "expected_answer": expected_answer,
            "actual_answer": answer,
        }
        case_results.append(case_row)
        metrics_input.append(
            {
                "retrieval_precision": precision,
                "response_correctness": correctness,
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

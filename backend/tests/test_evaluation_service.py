import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import app.services.evaluation_service as evaluation_service
from app.services.evaluation_service import compute_system_metrics, score_context_followup_from_payload


class EvaluationServiceTests(unittest.TestCase):
    def test_compute_metrics_includes_followup_accuracy(self):
        metrics = compute_system_metrics(
            [
                {
                    "retrieval_precision": 0.8,
                    "response_correctness": 0.6,
                    "context_followup_correctness": 1.0,
                    "context_application_rate": 1.0,
                },
                {
                    "retrieval_precision": 0.4,
                    "response_correctness": 0.2,
                    "context_followup_correctness": 0.0,
                    "context_application_rate": 0.0,
                },
            ]
        )

        self.assertIn("context_followup_accuracy", metrics)
        self.assertIn("context_application_rate", metrics)
        self.assertAlmostEqual(0.5, metrics["context_followup_accuracy"], places=4)
        self.assertAlmostEqual(0.5, metrics["context_application_rate"], places=4)

    def test_compute_metrics_defaults_followup_metric(self):
        metrics = compute_system_metrics(
            [
                {
                    "retrieval_precision": 1.0,
                    "response_correctness": 1.0,
                }
            ]
        )

        self.assertEqual(0.0, metrics["context_followup_accuracy"])

    def test_score_context_followup_payload_applied(self):
        payload = {
            "context_meta": {
                "query_context_applied": True,
                "temporal_context_applied": False,
                "gate": {
                    "applied": True,
                    "reason": "applied",
                },
            }
        }

        self.assertEqual(1.0, score_context_followup_from_payload(payload))

    def test_score_context_followup_payload_not_applied(self):
        payload = {
            "context_meta": {
                "query_context_applied": False,
                "temporal_context_applied": False,
                "gate": {
                    "applied": False,
                    "reason": "not_followup",
                },
            }
        }

        self.assertEqual(0.0, score_context_followup_from_payload(payload))

    def test_context_scenario_history_append_and_read(self):
        with TemporaryDirectory() as tmpdir:
            old_path = evaluation_service.CONTEXT_SCENARIO_HISTORY_PATH
            evaluation_service.CONTEXT_SCENARIO_HISTORY_PATH = Path(tmpdir) / "context_history.jsonl"
            try:
                evaluation_service._append_context_scenario_history(
                    {
                        "run_id": "ctx_run_a",
                        "context_followup_correctness": 1.0,
                        "gate_reason": "applied",
                    }
                )
                evaluation_service._append_context_scenario_history(
                    {
                        "run_id": "ctx_run_b",
                        "context_followup_correctness": 0.0,
                        "gate_reason": "not_followup",
                    }
                )

                history = evaluation_service.get_context_scenario_history(limit=5)
                self.assertEqual(2, history["count"])
                self.assertEqual("ctx_run_a", history["items"][0]["run_id"])
                self.assertEqual("ctx_run_b", history["items"][1]["run_id"])
                self.assertAlmostEqual(0.5, history["avg_context_followup_correctness"], places=4)
            finally:
                evaluation_service.CONTEXT_SCENARIO_HISTORY_PATH = old_path

    def test_context_scenario_history_limit(self):
        with TemporaryDirectory() as tmpdir:
            old_path = evaluation_service.CONTEXT_SCENARIO_HISTORY_PATH
            evaluation_service.CONTEXT_SCENARIO_HISTORY_PATH = Path(tmpdir) / "context_history.jsonl"
            try:
                for i in range(5):
                    evaluation_service._append_context_scenario_history(
                        {
                            "run_id": f"ctx_run_{i}",
                            "context_followup_correctness": float(i % 2),
                        }
                    )

                history = evaluation_service.get_context_scenario_history(limit=3)
                self.assertEqual(3, history["count"])
                self.assertEqual(["ctx_run_2", "ctx_run_3", "ctx_run_4"], [row["run_id"] for row in history["items"]])
            finally:
                evaluation_service.CONTEXT_SCENARIO_HISTORY_PATH = old_path


if __name__ == "__main__":
    unittest.main()

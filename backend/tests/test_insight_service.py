import unittest
from types import SimpleNamespace

from app.services.insight_service import analyze_insights


class InsightServiceTests(unittest.TestCase):
    def test_analyze_insights_includes_priority_signals(self):
        memories = [
            SimpleNamespace(
                type="habit",
                date="2026-04-20",
                time="08:00",
                content="Drank water",
                duration="20 min",
            ),
            SimpleNamespace(
                type="decision",
                date="2026-04-21",
                time="10:00",
                content="Important project deadline decision and planning",
                duration="2 hours",
            ),
            SimpleNamespace(
                type="mistake",
                date="2026-04-22",
                time="11:00",
                content="Critical mistake fix for the interview prep",
                duration="1 hour",
            ),
        ]

        result = analyze_insights(memories)

        self.assertEqual("ready", result["status"])
        self.assertGreater(result["priority_count"], 0)
        self.assertGreater(result["priority_ratio"], 0.0)
        self.assertIsNotNone(result["priority_focus"])
        self.assertTrue(result["priority_highlights"])
        self.assertIn("High-priority memories", result["insight"])

    def test_analyze_insights_handles_insufficient_data(self):
        result = analyze_insights([])

        self.assertEqual("insufficient_data", result["status"])
        self.assertEqual(0, result["priority_count"])
        self.assertEqual([], result["priority_highlights"])


if __name__ == "__main__":
    unittest.main()
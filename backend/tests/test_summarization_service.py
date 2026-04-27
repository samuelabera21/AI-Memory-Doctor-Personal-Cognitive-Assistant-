import unittest
from types import SimpleNamespace

from app.services.summarization_service import summarize_memories


class SummarizationServiceTests(unittest.TestCase):
    def test_summarize_memories_prioritizes_high_value_entries(self):
        memories = [
            SimpleNamespace(
                type="habit",
                date="2026-04-01",
                time="09:00",
                content="Drank water and took a walk",
                duration="30 min",
            ),
            SimpleNamespace(
                type="decision",
                date="2026-04-26",
                time="10:00",
                content="Important deadline project meeting and final decision",
                duration="2 hours",
            ),
            SimpleNamespace(
                type="mistake",
                date="2026-04-26",
                time="11:00",
                content="Critical mistake fix for the exam plan",
                duration="1 hour",
            ),
        ]

        summary = summarize_memories(memories)

        self.assertIn("Priority memories: 2.", summary)
        self.assertIn("Priority themes:", summary)
        self.assertIn("Key highlights:", summary)
        self.assertIn("decision", summary)

    def test_summarize_memories_handles_empty_input(self):
        self.assertEqual("No memories found for this period.", summarize_memories([]))


if __name__ == "__main__":
    unittest.main()
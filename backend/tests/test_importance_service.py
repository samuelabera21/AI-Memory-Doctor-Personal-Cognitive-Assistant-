import unittest
from types import SimpleNamespace

from app.services.importance_service import compute_importance_score, explain_importance
from app.services.ranking_service import rank_memories


class ImportanceServiceTests(unittest.TestCase):
    def test_compute_importance_scores_important_items_higher(self):
        urgent_memory = SimpleNamespace(
            type="decision",
            date="2026-04-26",
            time="09:00",
            content="Important deadline meeting for project",
            duration="2 hours",
        )
        plain_memory = SimpleNamespace(
            type="habit",
            date="2025-01-01",
            time="09:00",
            content="Drank water",
            duration=None,
        )

        self.assertGreater(compute_importance_score(urgent_memory), compute_importance_score(plain_memory))

    def test_explain_importance_returns_key_reasons(self):
        memory = SimpleNamespace(
            type="mistake",
            date="2026-04-25",
            time="10:00",
            content="Important mistake and deadline fix",
            duration="3 hours",
        )

        reasons = explain_importance(memory)

        self.assertIn("type:mistake", reasons)
        self.assertIn("recent", reasons)
        self.assertIn("duration", reasons)

    def test_rank_memories_prioritizes_high_importance_when_semantic_is_equal(self):
        urgent_memory = SimpleNamespace(
            id=1,
            type="decision",
            date="2026-04-26",
            time="09:00",
            content="Important deadline meeting for project",
            duration="2 hours",
        )
        plain_memory = SimpleNamespace(
            id=2,
            type="habit",
            date="2026-04-26",
            time="09:00",
            content="Drank water",
            duration=None,
        )

        ranked = rank_memories(query="project decision", memories=[plain_memory, urgent_memory], semantic_scores={1: 0.0, 2: 0.0})

        self.assertEqual(1, ranked[0].id)


if __name__ == "__main__":
    unittest.main()

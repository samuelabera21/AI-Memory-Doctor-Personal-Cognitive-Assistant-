import unittest
from types import SimpleNamespace

from app.services.conversation_service import get_context, normalize_query_with_context, update_context


class ConversationServiceTests(unittest.TestCase):
    def test_followup_query_is_enriched_from_previous_context(self):
        user_id = 11001
        memories = [
            SimpleNamespace(id=1, type="activity"),
            SimpleNamespace(id=2, type="goal"),
        ]
        update_context(user_id=user_id, query="What study activities did I do this week?", memories=memories)

        enriched = normalize_query_with_context(user_id=user_id, query="What about last week?")

        self.assertIn("about", enriched.lower())
        self.assertIn("study", enriched.lower())
        self.assertIn("activity", enriched.lower())

    def test_non_followup_query_is_not_changed(self):
        user_id = 11002
        update_context(
            user_id=user_id,
            query="Show my decisions this month",
            memories=[SimpleNamespace(id=3, type="decision")],
        )

        query = "What did I do yesterday?"
        enriched = normalize_query_with_context(user_id=user_id, query=query)

        self.assertEqual(query, enriched)

    def test_context_is_isolated_per_user(self):
        user_one = 12001
        user_two = 12002

        update_context(
            user_id=user_one,
            query="Show my study routines",
            memories=[SimpleNamespace(id=10, type="habit")],
        )
        update_context(
            user_id=user_two,
            query="Show my event timeline",
            memories=[SimpleNamespace(id=11, type="event")],
        )

        user_one_followup = normalize_query_with_context(user_id=user_one, query="what about last week?")
        user_two_followup = normalize_query_with_context(user_id=user_two, query="what about last week?")

        self.assertNotEqual(user_one_followup, user_two_followup)
        self.assertIn("habit", user_one_followup.lower())
        self.assertIn("event", user_two_followup.lower())

    def test_context_snapshot_contains_expected_fields(self):
        user_id = 13001
        update_context(
            user_id=user_id,
            query="I studied NLP in the morning",
            memories=[SimpleNamespace(id=21, type="activity")],
        )

        snapshot = get_context(user_id)

        self.assertIn("last_query", snapshot)
        self.assertIn("last_topic_terms", snapshot)
        self.assertIn("last_types", snapshot)
        self.assertIn("last_result_ids", snapshot)


if __name__ == "__main__":
    unittest.main()

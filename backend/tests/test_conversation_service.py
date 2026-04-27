import unittest
import time
from types import SimpleNamespace

import app.services.conversation_service as conversation_service

from app.services.conversation_service import (
    get_context,
    get_context_observability,
    merge_time_filters_with_context,
    normalize_query_with_context,
    reset_context_store,
    update_context,
)


class ConversationServiceTests(unittest.TestCase):
    def setUp(self):
        reset_context_store()

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
            time_filters={"start_date": "2026-04-20", "end_date": "2026-04-26", "start_time": None, "end_time": None},
        )

        snapshot = get_context(user_id)

        self.assertIn("last_query", snapshot)
        self.assertIn("last_topic_terms", snapshot)
        self.assertIn("last_types", snapshot)
        self.assertIn("last_result_ids", snapshot)
        self.assertIn("last_time_filters", snapshot)

    def test_followup_inherits_previous_date_range(self):
        user_id = 14001
        update_context(
            user_id=user_id,
            query="What did I do this week?",
            memories=[SimpleNamespace(id=31, type="activity")],
            time_filters={"start_date": "2026-04-20", "end_date": "2026-04-26", "start_time": None, "end_time": None},
        )

        merged = merge_time_filters_with_context(
            user_id=user_id,
            query="and in the morning?",
            time_filters={"start_date": None, "end_date": None, "start_time": "05:00", "end_time": "11:59"},
        )

        self.assertEqual("2026-04-20", merged["start_date"])
        self.assertEqual("2026-04-26", merged["end_date"])
        self.assertEqual("05:00", merged["start_time"])

    def test_non_followup_does_not_inherit_date_range(self):
        user_id = 14002
        update_context(
            user_id=user_id,
            query="What did I do this week?",
            memories=[SimpleNamespace(id=32, type="activity")],
            time_filters={"start_date": "2026-04-20", "end_date": "2026-04-26", "start_time": None, "end_time": None},
        )

        raw = {"start_date": None, "end_date": None, "start_time": None, "end_time": None}
        merged = merge_time_filters_with_context(
            user_id=user_id,
            query="What did I do yesterday?",
            time_filters=raw,
        )

        self.assertEqual(raw, merged)

    def test_expired_context_is_not_applied_to_followup(self):
        user_id = 15001
        old_ts = time.time() - (21 * 60)
        update_context(
            user_id=user_id,
            query="Show my study activities this week",
            memories=[SimpleNamespace(id=41, type="activity")],
            time_filters={"start_date": "2026-04-20", "end_date": "2026-04-26", "start_time": None, "end_time": None},
            updated_at_ts=old_ts,
        )

        query = "what about in the morning?"
        normalized = normalize_query_with_context(user_id=user_id, query=query)
        merged = merge_time_filters_with_context(
            user_id=user_id,
            query=query,
            time_filters={"start_date": None, "end_date": None, "start_time": "05:00", "end_time": "11:59"},
        )

        self.assertEqual(query, normalized)
        self.assertIsNone(merged["start_date"])
        self.assertIsNone(merged["end_date"])

    def test_low_confidence_context_is_not_applied(self):
        user_id = 15002
        update_context(
            user_id=user_id,
            query="this and that",
            memories=[],
            time_filters={"start_date": "2026-04-20", "end_date": "2026-04-26", "start_time": None, "end_time": None},
            updated_at_ts=time.time(),
        )

        query = "what about last week?"
        normalized = normalize_query_with_context(user_id=user_id, query=query)

        self.assertEqual(query, normalized)

    def test_observability_reports_expired_reason(self):
        user_id = 16001
        old_ts = time.time() - (25 * 60)
        update_context(
            user_id=user_id,
            query="Show my activities this week",
            memories=[SimpleNamespace(id=51, type="activity")],
            time_filters={"start_date": "2026-04-20", "end_date": "2026-04-26", "start_time": None, "end_time": None},
            updated_at_ts=old_ts,
        )

        meta = get_context_observability(user_id=user_id, query="what about morning?")

        self.assertFalse(meta["applied"])
        self.assertEqual("context_expired", meta["reason"])

    def test_observability_reports_applied_for_valid_followup(self):
        user_id = 16002
        update_context(
            user_id=user_id,
            query="What study activities did I do this week?",
            memories=[SimpleNamespace(id=52, type="activity")],
            time_filters={"start_date": "2026-04-20", "end_date": "2026-04-26", "start_time": None, "end_time": None},
            updated_at_ts=time.time(),
        )

        meta = get_context_observability(user_id=user_id, query="what about last week?")

        self.assertTrue(meta["applied"])
        self.assertEqual("applied", meta["reason"])

    def test_stale_context_is_pruned_from_store(self):
        user_id = 17001
        old_ts = time.time() - (30 * 60)
        update_context(
            user_id=user_id,
            query="Show my routines",
            memories=[SimpleNamespace(id=61, type="habit")],
            time_filters={"start_date": "2026-04-20", "end_date": "2026-04-26", "start_time": None, "end_time": None},
            updated_at_ts=old_ts,
        )

        snapshot = get_context(user_id)
        self.assertEqual({}, snapshot)

    def test_context_store_respects_max_user_cap(self):
        old_cap = conversation_service.CONTEXT_MAX_USERS
        conversation_service.CONTEXT_MAX_USERS = 2
        try:
            now = time.time()
            update_context(
                user_id=18001,
                query="user one",
                memories=[SimpleNamespace(id=71, type="activity")],
                updated_at_ts=now - 2,
            )
            update_context(
                user_id=18002,
                query="user two",
                memories=[SimpleNamespace(id=72, type="activity")],
                updated_at_ts=now - 1,
            )
            update_context(
                user_id=18003,
                query="user three",
                memories=[SimpleNamespace(id=73, type="activity")],
                updated_at_ts=now,
            )

            # Oldest user should be dropped when cap is exceeded.
            self.assertEqual({}, get_context(18001))
            self.assertNotEqual({}, get_context(18002))
            self.assertNotEqual({}, get_context(18003))
        finally:
            conversation_service.CONTEXT_MAX_USERS = old_cap


if __name__ == "__main__":
    unittest.main()

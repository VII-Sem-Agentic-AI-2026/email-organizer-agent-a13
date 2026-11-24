import unittest
from graph import EmailOrganizerGraph
from models import GraphState

class GraphTests(unittest.TestCase):
    def test_one_run_produces_validated_triaged_inbox(self):
        state = EmailOrganizerGraph().run(GraphState("T1"))
        self.assertTrue(state.validation_passed)
        self.assertEqual(len(state.triaged), 3)
        self.assertEqual(state.review_status, "PENDING_OWNER_REVIEW")

    def test_pipeline_runs_all_specialist_nodes(self):
        state = EmailOrganizerGraph().run(GraphState("T2"))
        expected = [
            "ingestion_classification", "priority_urgency", "draft_reply",
            "action_item_extraction", "follow_up_reminder",
            "calendar_task_sync", "validate_pass", "assemble",
            "owner_review_gate", "publish_blocked"
        ]
        for node in expected:
            self.assertIn(node, state.trace)

    def test_publish_is_blocked_without_owner_approval(self):
        state = EmailOrganizerGraph().run(GraphState("T3"), owner_approval=False)
        self.assertEqual(state.publish_status, "BLOCKED_PENDING_APPROVAL")
        self.assertNotIn("simulated_publish", state.trace)

    def test_publish_is_simulated_only_after_approval(self):
        state = EmailOrganizerGraph().run(GraphState("T4"), owner_approval=True)
        self.assertEqual(state.review_status, "APPROVED")
        self.assertEqual(state.publish_status, "SIMULATED_PUBLISHED")
        self.assertIn("simulated_publish", state.trace)

    def test_retry_limit_must_be_positive(self):
        with self.assertRaises(ValueError):
            EmailOrganizerGraph(max_attempts=0)

    def test_action_items_remain_pending(self):
        state = EmailOrganizerGraph().run(GraphState("T5"))
        self.assertTrue(all(x["status"] == "Pending" for x in state.action_items))

if __name__ == "__main__":
    unittest.main()

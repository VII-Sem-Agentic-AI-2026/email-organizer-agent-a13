import unittest
from models import MemoryItem, RunState
from memory_store import MemoryStore, MemoryAgent
from agent import EmailMemoryAgent, build_demo_store

class MemoryTests(unittest.TestCase):
    def setUp(self):
        self.store = build_demo_store()

    def test_tag_retrieval_returns_matching_tags(self):
        hits = self.store.retrieve_by_tags(["student", "project"])
        self.assertGreater(len(hits), 0)
        self.assertTrue(all(set(h.matched_tags) for h in hits))

    def test_similarity_retrieval_ranks_relevant_history(self):
        hits = self.store.retrieve_similar(
            "student project submission extension deadline", k=2
        )
        self.assertGreater(len(hits), 0)
        self.assertEqual(hits[0].item.item_id, "H001")

    def test_top_k_is_respected(self):
        hits = self.store.retrieve_similar("student project", k=1)
        self.assertLessEqual(len(hits), 1)

    def test_run_state_is_separate_from_archive(self):
        before = len(self.store.all_items())
        state = RunState(current_draft="A new draft")
        self.assertEqual(len(self.store.all_items()), before)
        self.assertEqual(state.current_draft, "A new draft")

    def test_memory_agent_returns_both_retrieval_types(self):
        result = MemoryAgent(self.store).retrieve(
            ["student"], "project submission extension", k=3
        )
        self.assertIn("tagged", result)
        self.assertIn("similar", result)

    def test_email_agent_does_not_store_current_draft(self):
        agent = EmailMemoryAgent(self.store)
        before = len(self.store.all_items())
        state, _ = agent.run()
        self.assertEqual(state.current_email_id, "CURRENT-001")
        self.assertEqual(len(self.store.all_items()), before)

    def test_add_rejects_untyped_item(self):
        with self.assertRaises(TypeError):
            self.store.add({"text": "not a MemoryItem"})

if __name__ == "__main__":
    unittest.main()

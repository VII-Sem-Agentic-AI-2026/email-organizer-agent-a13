import unittest
from models import EmailThread
from runtime import ResilientEmailRuntime

class ResilienceTests(unittest.TestCase):
    def setUp(self):
        self.threads = [
            EmailThread("A", "Asha", "Assignment", "Need clarification."),
            EmailThread("B", "Dev", "Meeting", "Can we meet?"),
        ]

    def test_injected_faults_are_repaired(self):
        result = ResilientEmailRuntime(2).run(self.threads, {
            "A": {"wrong_citation": True},
            "B": {"unauthorized_send": True},
        })
        self.assertTrue(result.passed)
        self.assertEqual(result.attempts, 1)
        self.assertEqual(result.drafts[0].cited_thread_id, "A")
        self.assertFalse(result.drafts[1].send_requested)

    def test_unaffected_body_is_not_rebuilt(self):
        result = ResilientEmailRuntime(2).run(self.threads, {
            "A": {"wrong_citation": True},
        })
        self.assertIn("Asha", result.drafts[0].body)
        self.assertEqual(result.drafts[0].repair_history,
                         ["Restored the correct thread citation"])

    def test_retry_budget_exhaustion_is_reported(self):
        # A zero retry budget leaves injected faults visible for escalation.
        result = ResilientEmailRuntime(0).run(self.threads, {
            "A": {"wrong_citation": True},
        })
        self.assertFalse(result.passed)
        self.assertTrue(any("exhausted" in x for x in result.diagnosis_log))

    def test_valid_run_passes_without_repair(self):
        result = ResilientEmailRuntime(2).run(self.threads)
        self.assertTrue(result.passed)
        self.assertEqual(result.attempts, 0)

if __name__ == "__main__":
    unittest.main()

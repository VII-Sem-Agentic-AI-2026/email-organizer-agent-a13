import unittest
from models import Email, LockedPlan
from factory import EmailOrganizerFactory

class FactoryTests(unittest.TestCase):
    def setUp(self):
        self.emails = [
            Email("A", "Asha", "Assignment", "Need help.", "HIGH"),
            Email("B", "Dev", "Meeting", "Can we meet?", "NORMAL"),
        ]
        self.factory = EmailOrganizerFactory()

    def test_valid_build_passes_all_checks(self):
        result = self.factory.build(self.emails)
        self.assertTrue(result["report"].all_pass)
        self.assertTrue(result["ready_for_owner_review"])

    def test_missing_citation_blocks_review(self):
        result = self.factory.build(self.emails, fault="missing_citation")
        self.assertFalse(result["report"].all_pass)
        self.assertFalse(result["ready_for_owner_review"])

    def test_auto_send_fault_blocks_review(self):
        result = self.factory.build(self.emails, fault="auto_send")
        self.assertFalse(result["report"].all_pass)
        self.assertFalse(result["ready_for_owner_review"])

    def test_empty_draft_blocks_review(self):
        result = self.factory.build(self.emails, fault="empty_draft")
        self.assertFalse(result["report"].all_pass)
        self.assertFalse(result["ready_for_owner_review"])

    def test_each_input_is_included_once(self):
        result = self.factory.build(self.emails)
        ids = [item.thread_id for item in result["artifact"].items]
        self.assertEqual(ids, ["A", "B"])

if __name__ == "__main__":
    unittest.main()

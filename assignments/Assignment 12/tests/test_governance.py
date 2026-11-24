import unittest
from models import Actor, DraftPackage, Status
from governance import GovernanceManager, GovernanceError

class GovernanceTests(unittest.TestCase):
    def setUp(self):
        self.owner = Actor("owner", "mailbox_owner")
        self.reviewer = Actor("reviewer", "reviewer")
        self.guest = Actor("guest", "guest")
        self.gov = GovernanceManager()
        self.draft = DraftPackage("P1", "Initial draft")

    def test_guest_cannot_view_confidential_draft(self):
        with self.assertRaises(GovernanceError):
            self.gov.view(self.draft, self.guest)

    def test_reviewer_can_view_but_cannot_approve(self):
        self.assertEqual(self.gov.view(self.draft, self.reviewer).body, "Initial draft")
        with self.assertRaises(GovernanceError):
            self.gov.approve(self.draft, self.reviewer)

    def test_only_owner_can_publish_approved_draft(self):
        self.gov.approve(self.draft, self.owner)
        with self.assertRaises(GovernanceError):
            self.gov.publish(self.draft, self.reviewer)
        result = self.gov.publish(self.draft, self.owner)
        self.assertEqual(result.status, Status.PUBLISHED)

    def test_publish_requires_approval(self):
        with self.assertRaises(GovernanceError):
            self.gov.publish(self.draft, self.owner)

    def test_rollback_restores_previous_version(self):
        self.gov.approve(self.draft, self.owner)
        first = self.gov.publish(self.draft, self.owner)
        second = DraftPackage("P1", "Second draft")
        self.gov.approve(second, self.owner)
        self.gov.publish(second, self.owner)
        restored = self.gov.rollback(first.version, self.owner)
        self.assertEqual(restored.body, "Initial draft")
        self.assertEqual(self.gov.metrics.rollbacks, 1)

    def test_non_owner_cannot_rollback(self):
        self.gov.approve(self.draft, self.owner)
        first = self.gov.publish(self.draft, self.owner)
        with self.assertRaises(GovernanceError):
            self.gov.rollback(first.version, self.reviewer)

    def test_audit_and_metrics_record_events(self):
        with self.assertRaises(GovernanceError):
            self.gov.view(self.draft, self.guest)
        self.assertGreaterEqual(len(self.gov.audit), 1)
        self.assertEqual(self.gov.evaluation_report()["rejected_actions"], 1)

if __name__ == "__main__":
    unittest.main()

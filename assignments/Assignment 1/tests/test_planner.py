import unittest
from main import EmailOrganizerCoordinator, EmailRequest


class PlannerTests(unittest.TestCase):
    def setUp(self):
        self.coordinator = EmailOrganizerCoordinator()

    def test_plan_contains_email_workflow(self):
        details = EmailRequest(
            request="Organize faculty inbox",
            folders=["inbox"],
            priority_rules=["deadlines"],
            output_format="triaged inbox",
        )
        plan = self.coordinator.create_plan(details)
        self.assertTrue(any("Read emails" in step for step in plan.steps))
        self.assertTrue(any("reply drafts" in step for step in plan.steps))
        self.assertTrue(any("review queue" in step for step in plan.steps))

    def test_plan_has_human_approval_constraint(self):
        details = EmailRequest("Organize inbox", ["inbox"], ["urgent"], "summary")
        plan = self.coordinator.create_plan(details)
        self.assertTrue(any("approval" in rule.lower() for rule in plan.constraints))

    def test_revision_adds_feedback(self):
        details = EmailRequest("Organize inbox", ["inbox"], ["urgent"], "summary")
        plan = self.coordinator.create_plan(details)
        revised = self.coordinator.revise(plan, "Include unread emails first")
        self.assertIn("Include unread emails first", revised.revision_notes)
        self.assertTrue(any("unread emails first" in step for step in revised.steps))


if __name__ == "__main__":
    unittest.main()

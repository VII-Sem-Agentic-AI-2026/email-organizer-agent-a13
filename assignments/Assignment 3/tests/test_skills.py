import unittest
from models import PlanInputs, TriageResult, TriagedEmail, TemplateSpec
from skills import plan_skill, format_triaged_skill

class SkillTests(unittest.TestCase):
    def test_plan_skill_returns_locked_plan(self):
        inputs = PlanInputs(
            request="Organize student emails",
            folders=["student-queries"],
            priority_rules=["Deadlines first"]
        )
        plan = plan_skill(inputs)
        self.assertTrue(plan.locked)
        self.assertGreater(len(plan.steps), 0)
        self.assertIn("Deadlines first", plan.priority_rules)

    def test_same_plan_skill_handles_second_case(self):
        first = plan_skill(PlanInputs("Organize student emails", ["students"]))
        second = plan_skill(PlanInputs("Organize admin emails", ["admin"]))
        self.assertNotEqual(first.goal, second.goal)
        self.assertEqual(first.steps, second.steps)

    def test_plan_skill_rejects_wrong_input_type(self):
        with self.assertRaises(TypeError):
            plan_skill({"request": "not typed"})

    def test_plan_skill_rejects_empty_request(self):
        with self.assertRaises(ValueError):
            plan_skill(PlanInputs(" "))

    def test_format_skill_renders_email_and_draft(self):
        result = TriageResult("Inbox", [
            TriagedEmail(
                "student@example.com", "Project deadline", "High",
                "Student", "Reply", "Please submit by Friday."
            )
        ])
        doc = format_triaged_skill(result, TemplateSpec())
        self.assertIn("Project deadline", doc.content)
        self.assertIn("Please submit by Friday.", doc.content)
        self.assertIn("approval", doc.sections)

    def test_same_format_skill_handles_different_case(self):
        first = TriageResult("A", [
            TriagedEmail("a@example.com", "Student query", "Medium",
                         "Student", "Reply", "Draft A")
        ])
        second = TriageResult("B", [
            TriagedEmail("b@example.com", "Admin notice", "High",
                         "Admin", "Review", "Draft B")
        ])
        doc_a = format_triaged_skill(first, TemplateSpec(title="Student Report"))
        doc_b = format_triaged_skill(second, TemplateSpec(title="Admin Report"))
        self.assertIn("Student Report", doc_a.content)
        self.assertIn("Admin Report", doc_b.content)
        self.assertIn("Draft A", doc_a.content)
        self.assertIn("Draft B", doc_b.content)

if __name__ == "__main__":
    unittest.main()

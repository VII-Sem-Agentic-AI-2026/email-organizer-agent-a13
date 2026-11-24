from models import PlanInputs, TriageResult, TemplateSpec
from skills import plan_skill, format_triaged_skill

class EmailOrganizerSkillAgent:
    """Invokes reusable planning and formatting skills."""
    def create_plan(self, inputs: PlanInputs):
        return plan_skill(inputs)

    def create_report(self, result: TriageResult, template: TemplateSpec):
        return format_triaged_skill(result, template)

    def run_demo(self):
        # Case 1: student-query folder and student-first rules.
        case_one = PlanInputs(
            request="Organize student queries and prepare draft replies.",
            folders=["student-queries"],
            priority_rules=["Deadlines first", "Escalations next"],
            outputs=["triaged list", "draft replies"]
        )

        # Case 2: administration folder and admin-first rules.
        # No change to either skill's implementation is required.
        case_two = PlanInputs(
            request="Organize administration emails and prepare draft replies.",
            folders=["admin"],
            priority_rules=["Admin deadlines first", "Urgent notices next"],
            outputs=["triaged list", "draft replies", "action items"]
        )

        sample = TriageResult(
            title="Sample inbox",
            emails=[
                # Demonstration record only; not fetched from a real mailbox.
                __import__("models").TriagedEmail(
                    sender="student@example.com",
                    subject="Project submission extension",
                    priority="Medium",
                    category="Student",
                    next_action="Review extension request",
                    draft_reply="Please share your reason and proposed submission date."
                )
            ]
        )

        plan_one = self.create_plan(case_one)
        plan_two = self.create_plan(case_two)
        report = self.create_report(sample, TemplateSpec())

        return plan_one, plan_two, report

"""
Assignment 1 - Agent vs Chatbot
Email Organizer Agent: plan -> act -> observe -> revise

This first lab demonstrates a coordinator loop. It does not connect to Gmail
or send messages. It creates an editable plan for organizing an inbox.
"""

from dataclasses import dataclass, field


@dataclass
class EmailRequest:
    request: str
    folders: list[str] = field(default_factory=list)
    priority_rules: list[str] = field(default_factory=list)
    output_format: str = "triaged inbox with draft replies"


@dataclass
class Plan:
    goal: str
    steps: list[str]
    constraints: list[str]
    revision_notes: list[str] = field(default_factory=list)

    def display(self):
        print("\n--- Proposed Email Organizer Plan ---")
        print(f"Goal: {self.goal}")
        print("\nSteps:")
        for i, step in enumerate(self.steps, 1):
            print(f"  {i}. {step}")
        print("\nConstraints:")
        for item in self.constraints:
            print(f"  - {item}")
        if self.revision_notes:
            print("\nRevision notes:")
            for note in self.revision_notes:
                print(f"  - {note}")


class EmailOrganizerCoordinator:
    """A small agent loop that clarifies, plans, observes feedback and revises."""

    def clarify(self, request_text: str) -> EmailRequest:
        print("\n[CLARIFY] I need a few details to prepare the inbox plan.")
        folders_text = input("Which folders should be organized? [inbox]: ").strip()
        folders = [x.strip() for x in folders_text.split(",") if x.strip()]
        if not folders:
            folders = ["inbox"]

        rules_text = input(
            "Priority rules (comma-separated) [deadlines, urgent requests]: "
        ).strip()
        rules = [x.strip() for x in rules_text.split(",") if x.strip()]
        if not rules:
            rules = ["deadlines", "urgent requests"]

        output = input(
            "Expected output [triaged inbox with draft replies]: "
        ).strip()
        if not output:
            output = "triaged inbox with draft replies"

        return EmailRequest(
            request=request_text,
            folders=folders,
            priority_rules=rules,
            output_format=output,
        )

    def create_plan(self, details: EmailRequest) -> Plan:
        print("\n[PLAN] Creating a step-by-step plan...")
        steps = [
            f"Read emails from: {', '.join(details.folders)}",
            "Identify sender category and email type",
            f"Rank emails using these priority rules: {', '.join(details.priority_rules)}",
            "Extract tasks, deadlines and meeting requests",
            "Prepare reply drafts for relevant emails",
            "Place drafts in a review queue for the mailbox owner",
            f"Present the result as: {details.output_format}",
        ]
        constraints = [
            "Do not send emails automatically",
            "Require mailbox-owner approval before sending",
            "Do not confirm meeting times without approval",
        ]
        return Plan(
            goal=f"Organize emails based on this request: {details.request}",
            steps=steps,
            constraints=constraints,
        )

    def act(self, plan: Plan):
        """For Lab 1, acting means preparing and displaying the editable plan."""
        print("\n[ACT] Preparing the proposed workflow...")
        plan.display()

    def observe(self) -> str:
        print("\n[OBSERVE] Review the plan above.")
        return input(
            "Enter feedback/change request, or press Enter if the plan is acceptable: "
        ).strip()

    def revise(self, plan: Plan, feedback: str) -> Plan:
        print("\n[REVISE] Updating the plan based on your feedback...")
        if not feedback:
            print("No changes requested. The plan is accepted as drafted.")
            return plan

        plan.revision_notes.append(feedback)
        plan.steps.append(f"Additional user-requested step: {feedback}")
        return plan

    def run(self):
        print("=" * 58)
        print("EMAIL ORGANIZER AGENT - ASSIGNMENT 1")
        print("Demonstration: Agent loop vs one-shot chatbot")
        print("=" * 58)

        request_text = input(
            "\nDescribe what you want the Email Organizer to do: "
        ).strip()
        if not request_text:
            request_text = "Organize my faculty inbox and prepare replies for review."

        details = self.clarify(request_text)
        plan = self.create_plan(details)
        self.act(plan)
        feedback = self.observe()
        plan = self.revise(plan, feedback)

        print("\n[FINAL OUTPUT] Editable plan")
        plan.display()
        print("\nCompleted. No Gmail access or email sending was performed.")


if __name__ == "__main__":
    EmailOrganizerCoordinator().run()

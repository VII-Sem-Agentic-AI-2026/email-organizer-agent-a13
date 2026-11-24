from dataclasses import dataclass, field


@dataclass
class EmailRequest:
    request: str
    folders: list[str]
    priority_rules: list[str]
    output_format: str


@dataclass
class Plan:
    goal: str
    steps: list[str]
    constraints: list[str]
    revision_notes: list[str] = field(default_factory=list)

    def display(self):
        print("\n===== EMAIL ORGANIZER PLAN =====")
        print("Goal:", self.goal)
        print("\nSteps:")
        for i, step in enumerate(self.steps, 1):
            print(f"{i}. {step}")
        print("\nConstraints:")
        for item in self.constraints:
            print("-", item)
        if self.revision_notes:
            print("\nRevision history:")
            for note in self.revision_notes:
                print("-", note)


class EmailOrganizerAgent:

    def clarify(self, request_text, input_fn=input):
        print("\n[CLARIFICATION]")
        print("I need more information before planning.")

        folders = input_fn("1. Which folders should I organize? [inbox]: ").strip()
        rules = input_fn(
            "2. What should determine priority? [deadlines, urgent requests]: "
        ).strip()
        output = input_fn(
            "3. What output do you need? [triaged inbox with draft replies]: "
        ).strip()

        return EmailRequest(
            request=request_text,
            folders=[x.strip() for x in (folders or "inbox").split(",") if x.strip()],
            priority_rules=[
                x.strip() for x in (rules or "deadlines, urgent requests").split(",")
                if x.strip()
            ],
            output_format=output or "triaged inbox with draft replies"
        )

    def create_plan(self, details):
        return Plan(
            goal=f"Organize faculty emails: {details.request}",
            steps=[
                f"Read emails from: {', '.join(details.folders)}",
                "Classify emails by sender category and content type",
                f"Rank emails using: {', '.join(details.priority_rules)}",
                "Extract tasks, deadlines and commitments",
                "Identify meeting requests",
                "Prepare reply drafts using the standard-response library where suitable",
                "Place drafts in the mailbox owner's review queue",
                f"Present the result as: {details.output_format}"
            ],
            constraints=[
                "Never send an email without explicit mailbox-owner approval",
                "Never confirm a meeting without approval",
                "Never mark a task complete without confirmation"
            ]
        )

    def revise(self, plan, feedback):
        feedback = feedback.strip()
        if not feedback:
            return plan

        lower = feedback.lower()

        if lower.startswith("add step:"):
            plan.steps.append(feedback.split(":", 1)[1].strip())

        elif lower.startswith("remove step "):
            try:
                number = int(lower.replace("remove step ", "").strip())
                if 1 <= number <= len(plan.steps):
                    plan.steps.pop(number - 1)
                else:
                    raise ValueError
            except ValueError:
                raise ValueError("Specify a valid step number.")

        elif lower.startswith("replace step "):
            try:
                left, replacement = feedback.split(" with ", 1)
                number = int(left.lower().replace("replace step ", "").strip())
                if 1 <= number <= len(plan.steps) and replacement.strip():
                    plan.steps[number - 1] = replacement.strip()
                else:
                    raise ValueError
            except ValueError:
                raise ValueError(
                    "Use: replace step NUMBER with NEW TEXT"
                )

        elif lower.startswith("change goal:"):
            plan.goal = feedback.split(":", 1)[1].strip()

        else:
            plan.steps.append("User-requested change: " + feedback)

        plan.revision_notes.append(feedback)
        return plan

    def run(self):
        print("EMAIL ORGANIZER AGENT - LAB 1")
        request = input("\nDescribe your request: ").strip()

        while not request:
            request = input("Please enter a request: ").strip()

        details = self.clarify(request)
        plan = self.create_plan(details)

        print("\n[PROPOSED PLAN]")
        plan.display()

        while True:
            feedback = input(
                "\nEnter feedback, or press Enter to accept the plan: "
            ).strip()

            if not feedback:
                break

            try:
                self.revise(plan, feedback)
                print("\n[REVISED PLAN]")
                plan.display()
            except ValueError as error:
                print("Revision error:", error)

        print("\n[FINAL ACCEPTED PLAN]")
        plan.display()
        print("\nLab 1 demonstration completed. No emails were accessed or sent.")


if __name__ == "__main__":
    EmailOrganizerAgent().run()

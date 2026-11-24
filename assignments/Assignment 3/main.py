from skills import (
    PlanInput, PlanBlueprintSkill, FormatTriagedSkill,
    TriageResult, TriagedEmail, TemplateSpec
)

planner = PlanBlueprintSkill()
formatter = FormatTriagedSkill()


def create_plan():
    print("\n===== PLAN / BLUEPRINT SKILL =====")

    case = input("Enter case name: ").strip()
    request = input("Describe the email organization task: ").strip()
    folders = input("Folders (comma separated): ").split(",")
    rules = input("Priority rules (comma separated): ").split(",")

    data = PlanInput(
        case_name=case,
        request=request,
        folders=[x.strip() for x in folders if x.strip()],
        priority_rules=[x.strip() for x in rules if x.strip()]
    )

    plan = planner.run(data)

    print("\n===== GENERATED PLAN =====")
    print("Case:", plan.case_name)
    print("Goal:", plan.goal)

    for i, step in enumerate(plan.steps, 1):
        print(f"{i}. {step}")

    print("\nConstraints:")
    for item in plan.constraints:
        print("-", item)

    print("\nPlan locked:", plan.locked)


def format_inbox():
    print("\n===== TRIAGED INBOX FORMATTING SKILL =====")

    case = input("Enter case name: ").strip()
    emails = []

    while True:
        print("\nEnter email details:")
        sender = input("Sender: ").strip()
        category = input("Category: ").strip()
        subject = input("Subject: ").strip()
        priority = input("Priority: ").strip()
        draft = input("Draft reply: ").strip()

        emails.append(TriagedEmail(
            sender=sender,
            category=category,
            subject=subject,
            priority=priority,
            draft_reply=draft
        ))

        more = input("\nAdd another email? (y/n): ").strip().lower()
        if more != "y":
            break

    result = TriageResult(case_name=case, emails=emails)

    template = TemplateSpec(
        title="Faculty Email Triage Report",
        include_drafts=True,
        include_priority=True
    )

    document = formatter.run(result, template)

    print("\n===== FORMATTED DOCUMENT =====")
    print(document.content)


def full_demo():
    print("\n===== REUSABILITY DEMONSTRATION =====")

    cases = [
        PlanInput(
            "Student Queries",
            "Organize student emails",
            ["inbox"],
            ["deadlines", "urgency"]
        ),
        PlanInput(
            "Administrative Emails",
            "Organize administrative emails",
            ["inbox", "admin"],
            ["official deadlines", "meeting dates"]
        )
    ]

    for data in cases:
        plan = planner.run(data)
        print("\nCase:", plan.case_name)
        print("Plan locked:", plan.locked)
        for i, step in enumerate(plan.steps, 1):
            print(f"{i}. {step}")

        result = TriageResult(
            case_name=data.case_name,
            emails=[
                TriagedEmail(
                    "faculty@college.edu",
                    "faculty",
                    "Email organization request",
                    "High",
                    "Thank you for your email. I will review it."
                )
            ]
        )

        document = formatter.run(
            result,
            TemplateSpec("Faculty Triage Report")
        )
        print("\n", document.content)

    print("\nSame two skills successfully reused for both cases.")


def main():
    while True:
        print("\n" + "=" * 48)
        print("       EMAIL ORGANIZER AGENT - LAB 3")
        print("=" * 48)
        print("1. Create Email Organization Plan")
        print("2. Format Triaged Inbox")
        print("3. Run Two-Case Reusability Demo")
        print("0. Exit")

        choice = input("\nEnter your choice: ").strip()

        if choice == "1":
            create_plan()
        elif choice == "2":
            format_inbox()
        elif choice == "3":
            full_demo()
        elif choice == "0":
            print("\nLab 3 completed. Goodbye!")
            break
        else:
            print("Invalid choice. Select 0, 1, 2 or 3.")


if __name__ == "__main__":
    main()

from models import Email, LockedPlan
from factory import EmailOrganizerFactory

def main():
    emails = [
        Email("TH-201", "Ananya", "Project extension",
              "Requesting two extra days for submission.", "HIGH"),
        Email("TH-202", "Rahul", "Meeting request",
              "Can we meet next week?", "NORMAL"),
        Email("TH-203", "Office", "Monthly notice",
              "Please read the attached notice.", "LOW"),
    ]
    plan = LockedPlan()
    result = EmailOrganizerFactory().build(emails, plan)

    print("EMAIL ORGANIZER — SDLC FACTORY")
    print("=" * 42)
    print("Build result:", "PASS" if result["report"].all_pass else "FAIL")
    print("\\nACCEPTANCE REPORT")
    for check in result["report"].checks:
        print(f"[{'PASS' if check.passed else 'FAIL'}] {check.name}: {check.detail}")

    print("\\nTRIAGED INBOX WITH DRAFT REPLIES")
    for item in result["artifact"].items:
        print(f"\\n{item.thread_id} | {item.priority} | {item.subject}")
        print(item.body)
        print("Evidence:", item.source_thread_id)
        print("Sent:", item.sent)

    print("\\nReady for mailbox owner review:",
          result["ready_for_owner_review"])
    print("No email is sent by this lab.")

if __name__ == "__main__":
    main()

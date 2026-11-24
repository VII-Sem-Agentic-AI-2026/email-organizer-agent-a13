from models import EmailThread
from runtime import ResilientEmailRuntime

def main():
    threads = [
        EmailThread("TH-101", "Ananya", "Project extension", "May I have two extra days?"),
        EmailThread("TH-102", "Rahul", "Meeting schedule", "Can we meet on Friday?"),
    ]

    faults = {
        "TH-101": {"wrong_citation": True},
        "TH-102": {"unauthorized_send": True},
    }

    result = ResilientEmailRuntime(max_attempts=2).run(threads, faults)

    print("EMAIL ORGANIZER - OPS RESILIENCE")
    print("=" * 42)
    print(f"Validation: {'PASSED' if result.passed else 'FAILED'}")
    print(f"Repair attempts: {result.attempts}")

    for line in result.diagnosis_log:
        print("-", line)

    print("\nFINAL DRAFTS")

    for draft in result.drafts:
        print(f"\n{draft.thread_id}: {draft.body}")
        print(f"Source thread: {draft.cited_thread_id}")
        print(f"Send requested: {draft.send_requested}")
        print(f"Repair history: {draft.repair_history}")

    print("\nNo email is sent. Owner approval is still required.")

if __name__ == "__main__":
    main()

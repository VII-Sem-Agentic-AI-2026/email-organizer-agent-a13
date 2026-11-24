from agent import EmailSwarmCoordinator
from models import EmailThread, LockedPlan

SAMPLE_EMAILS = [
    EmailThread("T-101", "student@example.com", "Project extension request",
                "I need an extension for the project submission tomorrow due to a technical issue."),
    EmailThread("T-102", "admin@example.com", "Urgent: report due today",
                "Please send the department report today before 4 PM."),
    EmailThread("T-103", "colleague@example.com", "Meeting next week",
                "Can we arrange a meeting next week to discuss the event plan?"),
    EmailThread("T-104", "student2@example.com", "Lab attendance query",
                "Could you clarify my lab attendance record?"),
]

def main():
    plan = LockedPlan()
    result, sequential_time, parallel_time = EmailSwarmCoordinator(4).execute(SAMPLE_EMAILS, plan)

    print("\nEMAIL ORGANIZER - PARALLEL SWARM (LAB 8)")
    print("=" * 48)
    print("Threads received:", len(SAMPLE_EMAILS))
    print("All threads processed and merged:", result.all_threads_processed)

    print("\nTIMING COMPARISON")
    print(f"Sequential: {sequential_time:.6f} seconds")
    print(f"Parallel:   {parallel_time:.6f} seconds")
    print("Parallel faster:", parallel_time < sequential_time)

    print("\nMERGED RESULTS")
    for item in result.selected:
        print(f"\n[{item.thread_id}] {item.subject} - {item.priority}")
        print("Selected worker:", item.selected_worker)
        print("Plan alignment:", item.alignment_score)
        print("Summary:", item.summary)
        print("Draft:", item.draft_reply.splitlines()[0])

    print("\nAll drafts are local examples. No email is sent.")

if __name__ == "__main__":
    main()

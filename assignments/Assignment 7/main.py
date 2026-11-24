import argparse
import json
from pathlib import Path
from graph import EmailOrganizerGraph
from models import GraphState

def main():
    parser = argparse.ArgumentParser(description="Lab 7 Email Organizer Node Graph")
    parser.add_argument(
        "--approve-demo", action="store_true",
        help="Simulate mailbox-owner approval and a non-sending publish step."
    )
    args = parser.parse_args()

    graph = EmailOrganizerGraph(max_attempts=2)
    state = graph.run(
        GraphState(run_id="LAB7-DEMO"),
        owner_approval=args.approve_demo
    )

    print("\\nLAB 7 — AGENTIC NODE GRAPH")
    print("=" * 44)
    print("Run:", state.run_id)
    print("Emails processed:", len(state.inbox))
    print("Validation passed:", state.validation_passed)
    print("Validation attempts:", state.attempts)
    print("Review status:", state.review_status)
    print("Publish status:", state.publish_status)

    print("\\nTRIAGED INBOX")
    for item in state.triaged:
        print(f"- [{item['priority']}] {item['subject']}")
        print(f"  Category: {item['category']} | Type: {item['type']}")
        print(f"  Draft: {item['draft_reply']}")

    print("\\nACTION ITEMS:", len(state.action_items))
    print("MEETING PROPOSALS:", len(state.meeting_proposals))
    print("FOLLOW-UPS:", len(state.follow_ups))
    print("\\nGRAPH TRACE:")
    print(" -> ".join(state.trace))

    output_path = Path("lab7_output.json")
    output_path.write_text(
        json.dumps(state.assembled_report or {
            "run_id": state.run_id,
            "validation_errors": state.validation_errors,
            "review_status": state.review_status,
            "publish_status": state.publish_status,
        }, indent=2),
        encoding="utf-8"
    )
    print("\\nSaved output:", output_path)
    print("No real email is sent. Use --approve-demo only to simulate approval.")

if __name__ == "__main__":
    main()

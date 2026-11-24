from models import AcceptanceReport, Check

def acceptance_suite(artifact, plan, input_emails):
    expected_ids = {email.thread_id for email in input_emails}
    actual_ids = [item.thread_id for item in artifact.items]
    checks = [
        Check("All input threads are represented",
              set(actual_ids) == expected_ids and len(actual_ids) == len(expected_ids),
              "Every input email must appear exactly once."),
        Check("Locked plan steps are followed",
              artifact.plan_steps == plan.required_steps,
              "Artifact must carry the required plan steps."),
        Check("Priority values follow the plan",
              all(item.priority in plan.allowed_priorities for item in artifact.items),
              "Every priority must be in the plan's allowed set."),
        Check("Every draft cites its own thread",
              all(item.source_thread_id == item.thread_id for item in artifact.items)
              if plan.require_thread_citation else True,
              "Each draft must point to the source thread."),
        Check("No email was sent automatically",
              all(not item.sent for item in artifact.items)
              if plan.prohibit_auto_send else True,
              "All replies must remain drafts for owner review."),
        Check("Every draft has reply content",
              all(bool(item.body.strip()) for item in artifact.items),
              "Draft body cannot be empty."),
    ]
    return AcceptanceReport(checks)

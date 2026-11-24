from models import GraphState
from agents import (
    ingestion_classification, priority_urgency, draft_reply,
    action_item_extraction, follow_up_reminder, calendar_task_sync,
    validate, regenerate_drafts, assemble,
)

class EmailOrganizerGraph:
    """
    Explicit sequential node graph with a bounded validation -> regenerate
    back-edge and a hard human review gate before simulated publishing.
    """
    def __init__(self, max_attempts=2):
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1.")
        self.max_attempts = max_attempts

    def run(self, state=None, owner_approval=False):
        state = state or GraphState(run_id="GRAPH-RUN-001", max_attempts=self.max_attempts)
        state.max_attempts = self.max_attempts

        ingestion_classification(state)
        priority_urgency(state)
        draft_reply(state)
        action_item_extraction(state)
        follow_up_reminder(state)
        calendar_task_sync(state)

        # Validation failure returns to draft generation, but never loops forever.
        while True:
            state.attempts += 1
            validate(state)
            if state.validation_passed:
                break
            if state.attempts >= state.max_attempts:
                state.review_status = "ESCALATED_VALIDATION_FAILED"
                state.trace.append("escalate")
                return state
            regenerate_drafts(state)

        assemble(state)
        state.review_status = "PENDING_OWNER_REVIEW"
        state.trace.append("owner_review_gate")

        if not owner_approval:
            state.publish_status = "BLOCKED_PENDING_APPROVAL"
            state.trace.append("publish_blocked")
            return state

        state.review_status = "APPROVED"
        state.trace.append("owner_approved")
        # Simulated publish only; no Gmail action occurs in this assignment.
        state.publish_status = "SIMULATED_PUBLISHED"
        state.trace.append("simulated_publish")
        return state

from models import Draft, EmailThread, ValidationIssue

class DraftAgent:
    def create(self, thread: EmailThread) -> Draft:
        return Draft(
            thread_id=thread.thread_id,
            body=f"Hello {thread.sender}, thank you for your email about {thread.subject}. I will review the details and get back to you.",
            cited_thread_id=thread.thread_id,
        )

class ValidationAgent:
    def validate(self, drafts):
        issues = []
        for draft in drafts:
            if draft.send_requested and not draft.approved:
                issues.append(ValidationIssue(draft.thread_id, "send_requested",
                    "A message cannot be sent without owner approval."))
            if not draft.cited_thread_id:
                issues.append(ValidationIssue(draft.thread_id, "cited_thread_id",
                    "Draft is missing its source thread reference."))
            elif draft.cited_thread_id != draft.thread_id:
                issues.append(ValidationIssue(draft.thread_id, "cited_thread_id",
                    "Draft cites a different email thread."))
        return issues

class RepairAgent:
    """Repairs only fields identified by the validation report."""
    def repair(self, draft, issue, thread):
        if issue.field == "send_requested":
            draft.send_requested = False
            draft.repair_history.append("Blocked sending until owner approval")
        elif issue.field == "cited_thread_id":
            draft.cited_thread_id = thread.thread_id
            # Keep the original draft body unchanged.
            draft.repair_history.append("Restored the correct thread citation")
        return draft

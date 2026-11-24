from models import DraftReply, InboxArtifact

def build_artifact(plan, emails):
    """Small deterministic build pipeline that follows the locked plan."""
    items = []
    for email in emails:
        priority = email.priority.upper()
        if priority not in plan.allowed_priorities:
            priority = "NORMAL"
        body = (
            f"Hello {email.sender}, thank you for contacting us about "
            f"{email.subject}. We have noted your message and will review it."
        )
        items.append(DraftReply(
            thread_id=email.thread_id,
            sender=email.sender,
            subject=email.subject,
            priority=priority,
            body=body,
            source_thread_id=email.thread_id,
            sent=False,
        ))
    return InboxArtifact(plan_steps=plan.required_steps, items=items)

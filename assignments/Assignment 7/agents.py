"""Deterministic specialist nodes for the Email Organizer graph."""

def ingestion_classification(state):
    # Local sample inbox. In the main project this data comes through the connector.
    state.inbox = [
        {
            "id": "E401", "sender": "student@example.com",
            "subject": "Request for project submission extension",
            "body": "Could I submit the project on Friday? I have a medical appointment.",
            "thread_history": ["Please share your reason and proposed submission date."],
            "tags": ["student", "project", "extension"],
        },
        {
            "id": "E402", "sender": "office@example.com",
            "subject": "Urgent: department report deadline",
            "body": "Please submit the department report by Thursday.",
            "thread_history": ["The report format was shared yesterday."],
            "tags": ["admin", "report", "deadline"],
        },
        {
            "id": "E403", "sender": "colleague@example.com",
            "subject": "Meeting request for research discussion",
            "body": "Can we meet next week to discuss the paper?",
            "thread_history": [],
            "tags": ["colleague", "meeting", "research"],
        },
    ]
    for email in state.inbox:
        subject = email["subject"].lower()
        body = email["body"].lower()
        if "office" in email["sender"]:
            category = "Administration"
        elif "student" in email["sender"]:
            category = "Student"
        else:
            category = "Colleague"

        if "meeting" in subject or "meet" in body:
            content_type = "Meeting Request"
        elif "deadline" in subject or "submit" in body:
            content_type = "Task / Submission"
        else:
            content_type = "General Query"

        email["sender_category"] = category
        email["content_type"] = content_type
    state.trace.append("ingestion_classification")
    return state

def priority_urgency(state):
    for email in state.inbox:
        text = (email["subject"] + " " + email["body"]).lower()
        if "urgent" in text or "by thursday" in text:
            priority = "High"
        elif "extension" in text or "meeting" in text:
            priority = "Medium"
        else:
            priority = "Low"
        email["priority"] = priority
    state.trace.append("priority_urgency")
    return state

def draft_reply(state):
    for email in state.inbox:
        prior = email["thread_history"]
        if email["content_type"] == "Meeting Request":
            draft = "Thank you. Please share your preferred dates and times so availability can be checked."
        elif email["sender_category"] == "Student":
            draft = "Thank you for explaining. Please confirm your proposed submission date for review."
        elif email["sender_category"] == "Administration":
            draft = "Thank you for the reminder. The report deadline has been noted."
        else:
            draft = "Thank you for your email. I will review this and get back to you."
        email["draft_reply"] = draft
        email["grounding_evidence"] = list(prior)
    state.trace.append("draft_reply")
    return state

def action_item_extraction(state):
    state.action_items = []
    for email in state.inbox:
        body = email["body"].lower()
        if any(word in body for word in ("submit", "deadline", "by thursday", "friday")):
            state.action_items.append({
                "email_id": email["id"],
                "task": email["subject"],
                "status": "Pending",
            })
    state.trace.append("action_item_extraction")
    return state

def follow_up_reminder(state):
    state.follow_ups = [
        {"email_id": email["id"], "reason": "Reply later requested or pending response"}
        for email in state.inbox
        if "reply later" in email["body"].lower()
    ]
    state.trace.append("follow_up_reminder")
    return state

def calendar_task_sync(state):
    state.meeting_proposals = [
        {
            "email_id": email["id"],
            "request": email["subject"],
            "proposal": "Check faculty calendar and propose available slots",
            "status": "Needs faculty confirmation",
        }
        for email in state.inbox
        if email["content_type"] == "Meeting Request"
    ]
    state.trace.append("calendar_task_sync")
    return state

def validate(state):
    errors = []
    if not state.inbox:
        errors.append("Inbox is empty.")
    for email in state.inbox:
        for field in ("sender_category", "content_type", "priority", "draft_reply"):
            if not email.get(field):
                errors.append(f"{email.get('id', 'unknown')}: missing {field}.")
        if not isinstance(email.get("grounding_evidence"), list):
            errors.append(f"{email.get('id', 'unknown')}: grounding evidence missing.")
    if any(item.get("status") != "Pending" for item in state.action_items):
        errors.append("Action items must remain pending until confirmed.")
    state.validation_errors = errors
    state.validation_passed = not errors
    state.trace.append("validate_pass" if state.validation_passed else "validate_fail")
    return state

def regenerate_drafts(state):
    # Bounded repair node: rebuild draft fields and rerun validation.
    draft_reply(state)
    state.trace.append("regenerate")
    return state

def assemble(state):
    state.triaged = [
        {
            "id": email["id"],
            "sender": email["sender"],
            "subject": email["subject"],
            "category": email["sender_category"],
            "type": email["content_type"],
            "priority": email["priority"],
            "draft_reply": email["draft_reply"],
            "grounding_evidence": email["grounding_evidence"],
        }
        for email in state.inbox
    ]
    state.assembled_report = {
        "run_id": state.run_id,
        "emails": state.triaged,
        "action_items": state.action_items,
        "follow_ups": state.follow_ups,
        "meeting_proposals": state.meeting_proposals,
        "validation_passed": state.validation_passed,
    }
    state.trace.append("assemble")
    return state

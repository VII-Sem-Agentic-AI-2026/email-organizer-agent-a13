"""Local mock tools. No external accounts or services are contacted."""

def read_inbox(inputs: dict) -> dict:
    emails = [
        {"id": "E301", "subject": "Project submission extension",
         "sender": "student@example.com"},
        {"id": "E302", "subject": "Department report deadline",
         "sender": "office@example.com"},
    ]
    return {"emails": emails, "email_count": len(emails)}

def retrieve_context(inputs: dict) -> dict:
    return {
        "prior_reply": "Please share your reason and proposed submission date.",
        "memory_source": "sample_history",
    }

def prepare_draft(inputs: dict) -> dict:
    return {
        "draft": "Thank you for your email. Please share your proposed submission date.",
        "requires_human_review": True,
    }

def publish_draft(inputs: dict) -> dict:
    # Deliberately simulated: never sends an actual email.
    return {"status": "SIMULATED_PUBLISH", "message": "No email was sent."}

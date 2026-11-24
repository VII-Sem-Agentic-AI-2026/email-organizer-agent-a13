"""Small reusable skills carried forward from Assignment 3."""

def make_plan(inputs: dict) -> dict:
    return {
        "goal": inputs.get("goal", "Triage inbox and prepare draft replies"),
        "steps": ["read_inbox", "retrieve_context", "prepare_draft", "publish"],
        "locked": True,
    }

def format_summary(data: dict) -> str:
    return (
        f"Inbox items: {data.get('email_count', 0)}\\n"
        f"Draft prepared: {data.get('draft', 'Not prepared')}"
    )

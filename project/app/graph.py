
from dataclasses import dataclass, field
from typing import TypedDict

from langgraph.graph import StateGraph, START, END

from tools import read_inbox
from retry import retry_operation
from classifier import classify_email_safe, extract_action_items_safe
from memory import get_grounding_context
from reminder_manager import ReminderManager


# Public state returned to existing project code.
@dataclass
class GraphState:
    emails: list = field(default_factory=list)
    classifications: list = field(default_factory=list)
    action_items: list = field(default_factory=list)
    triage_draft: list = field(default_factory=list)
    validation_passed: bool = False
    errors: list = field(default_factory=list)
    reminders: list = field(default_factory=list)


# State maintained by LangGraph.
class GraphData(TypedDict):
    emails: list
    classifications: list
    action_items: list
    triage_draft: list
    validation_passed: bool
    errors: list
    attempts: int
    reminders: list


def to_graph_state(data: dict) -> GraphState:
    return GraphState(
        emails=data.get("emails", []),
        classifications=data.get("classifications", []),
        action_items=data.get("action_items", []),
        triage_draft=data.get("triage_draft", []),
        validation_passed=data.get("validation_passed", False),
        errors=data.get("errors", []),
        reminders=data.get("reminders", []),
    )


# Existing processing functions

def ingest_inbox(state: GraphState) -> GraphState:
    state.emails = read_inbox()
    return state


def classify_emails(state: GraphState) -> GraphState:
    state.classifications = []

    for email in state.emails:
        classification = classify_email_safe(email)
        state.classifications.append({
            "sender_category": classification.sender_category,
            "email_type": classification.email_type,
            "priority": classification.priority,
        })

    return state


def schedule_reminders(state: GraphState, reminder_manager: ReminderManager = None) -> GraphState:
    """
    Deterministic LangGraph processing component that schedules persistent reminders
    for High and Critical priority emails right after classification.
    Zero LLM calls are made here.
    """
    if reminder_manager is None:
        reminder_manager = ReminderManager()

    scheduled = []
    for email, classification in zip(state.emails, state.classifications):
        priority = classification.get("priority", "Low")
        if priority.capitalize() in ("Critical", "High"):
            email_id = getattr(email, "message_id", None) or f"{email.sender}_{email.subject}"
            reminder = reminder_manager.create_reminder(
                email_id=email_id,
                sender=email.sender,
                subject=email.subject,
                body=email.body,
                priority=priority
            )
            if reminder:
                scheduled.append(reminder.to_dict())

    state.reminders = scheduled
    return state


def extract_actions(state: GraphState) -> GraphState:
    state.action_items = []

    for email in state.emails:
        extraction = extract_action_items_safe(email)
        state.action_items.append({
            "email": email,
            "action_items": extraction.action_items,
        })

    return state


def create_triage_draft(state: GraphState) -> GraphState:
    # Clear previous drafts so regeneration cannot duplicate them.
    state.triage_draft = []

    for email, classification, actions in zip(
        state.emails,
        state.classifications,
        state.action_items,
    ):
        state.triage_draft.append({
            "sender": email.sender,
            "subject": email.subject,
            "sender_category": classification["sender_category"],
            "email_type": classification["email_type"],
            "priority": classification["priority"],
            "action_items": actions["action_items"],
        })

    return state


def ground_triage(state: GraphState) -> GraphState:
    for draft, email in zip(state.triage_draft, state.emails):
        evidence = get_grounding_context(
            email.sender,
            email.subject,
            email.body,
        )
        draft["evidence"] = [
            item.content for item in evidence
        ]

    return state


def validate_triage(state: GraphState) -> GraphState:
    state.errors = []

    for index, draft in enumerate(state.triage_draft):
        if not draft.get("sender"):
            state.errors.append(f"Email {index}: missing sender")

        if not draft.get("subject"):
            state.errors.append(f"Email {index}: missing subject")

        if draft.get("priority") not in {
            "Critical", "High", "Medium", "Low"
        }:
            state.errors.append(f"Email {index}: invalid priority")

    state.validation_passed = len(state.errors) == 0
    return state


def validate_grounding(state: GraphState) -> GraphState:
    for index, draft in enumerate(state.triage_draft):
        if not draft.get("evidence"):
            state.errors.append(
                f"Email {index}: no supporting history evidence"
            )

    state.validation_passed = len(state.errors) == 0
    return state


def regenerate_triage(state: GraphState) -> GraphState:
    if state.validation_passed:
        return state

    print("\nRegenerating failed triage...")

    state = classify_emails(state)
    state = schedule_reminders(state)
    state = create_triage_draft(state)
    return state


# LangGraph node wrappers.
# Each node receives a dictionary and returns state updates.

def ingest_node(data: GraphData) -> dict:
    state = to_graph_state(data)
    state = ingest_inbox(state)
    return {"emails": state.emails}


def classify_node(data: GraphData) -> dict:
    state = to_graph_state(data)
    state = classify_emails(state)
    return {"classifications": state.classifications}


def schedule_reminders_node(data: GraphData) -> dict:
    state = to_graph_state(data)
    state = schedule_reminders(state)
    return {"reminders": state.reminders}


def extract_actions_node(data: GraphData) -> dict:
    state = to_graph_state(data)
    state = extract_actions(state)
    return {"action_items": state.action_items}


def create_draft_node(data: GraphData) -> dict:
    state = to_graph_state(data)
    state = create_triage_draft(state)
    return {"triage_draft": state.triage_draft}


def ground_node(data: GraphData) -> dict:
    state = to_graph_state(data)
    state = ground_triage(state)
    return {"triage_draft": state.triage_draft}


def validate_node(data: GraphData) -> dict:
    state = to_graph_state(data)
    state = validate_triage(state)
    state = validate_grounding(state)

    return {
        "validation_passed": state.validation_passed,
        "errors": state.errors,
        "triage_draft": state.triage_draft,
    }


def regenerate_node(data: GraphData) -> dict:
    state = to_graph_state(data)
    state.validation_passed = False
    state = regenerate_triage(state)

    return {
        "classifications": state.classifications,
        "triage_draft": state.triage_draft,
        "attempts": data["attempts"] + 1,
    }


# Conditional routing after validation.

def route_after_validation(data: GraphData) -> str:
    if data["validation_passed"]:
        return "end"

    if data["attempts"] >= 2:
        return "end"

    return "regenerate"


def build_graph():
    workflow = StateGraph(GraphData)

    workflow.add_node("ingest", ingest_node)
    workflow.add_node("classify", classify_node)
    workflow.add_node("schedule_reminders", schedule_reminders_node)
    workflow.add_node("extract_actions", extract_actions_node)
    workflow.add_node("create_draft", create_draft_node)
    workflow.add_node("ground", ground_node)
    workflow.add_node("validate", validate_node)
    workflow.add_node("regenerate", regenerate_node)

    workflow.add_edge(START, "ingest")
    workflow.add_edge("ingest", "classify")
    workflow.add_edge("classify", "schedule_reminders")
    workflow.add_edge("schedule_reminders", "extract_actions")
    workflow.add_edge("extract_actions", "create_draft")
    workflow.add_edge("create_draft", "ground")
    workflow.add_edge("ground", "validate")

    workflow.add_conditional_edges(
        "validate",
        route_after_validation,
        {
            "regenerate": "regenerate",
            "end": END,
        },
    )

    workflow.add_edge("regenerate", "ground")

    return workflow.compile()


# Keep the existing run_graph() interface for capstone.py.

def run_graph() -> GraphState:
    initial_state: GraphData = {
        "emails": [],
        "classifications": [],
        "action_items": [],
        "triage_draft": [],
        "validation_passed": False,
        "errors": [],
        "attempts": 0,
        "reminders": [],
    }

    result = build_graph().invoke(initial_state)
    return to_graph_state(result)


def test_regeneration():
    state = GraphState()
    state = ingest_inbox(state)

    if not state.emails:
        print("No emails available for the regeneration test.")
        return

    state = classify_emails(state)
    state = extract_actions(state)
    state = create_triage_draft(state)
    state = ground_triage(state)

    state.triage_draft[0]["priority"] = "INVALID"

    state = validate_triage(state)
    state = validate_grounding(state)

    print("Before regeneration:", state.validation_passed)
    print("Errors:", state.errors)

    if not state.validation_passed:
        state = regenerate_triage(state)
        state = ground_triage(state)
        state = validate_triage(state)
        state = validate_grounding(state)

    print("After regeneration:", state.validation_passed)
    print("Errors:", state.errors)


if __name__ == "__main__":
    result = run_graph()
    print("Emails processed:", len(result.emails))
    print("Validation passed:", result.validation_passed)
    print("Errors:", result.errors)

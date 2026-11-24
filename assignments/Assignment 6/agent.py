from models import AgentStep, RunState
from tools import read_inbox, retrieve_context, prepare_draft, publish_draft

def build_steps():
    return [
        AgentStep("S1", "Read incoming emails", "read_inbox", {}, read_inbox),
        AgentStep("S2", "Retrieve prior email context", "retrieve_context",
                  {"email_id": "E301"}, retrieve_context),
        AgentStep("S3", "Prepare a reply draft", "prepare_draft",
                  {"email_id": "E301"}, prepare_draft),
        AgentStep("S4", "Publish approved draft", "publish_draft",
                  {"draft_id": "D301"}, publish_draft, risky=True),
    ]

def new_run_state(run_id="EMAIL-RUN-001"):
    return RunState(run_id=run_id)

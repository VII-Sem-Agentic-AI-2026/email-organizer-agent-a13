from models import LockedPlan
from pipeline import build_artifact
from acceptance import acceptance_suite

class EmailOrganizerFactory:
    def build(self, emails, plan=None, fault=None):
        plan = plan or LockedPlan()
        artifact = build_artifact(plan, emails)

        # Optional failure injection demonstrates the acceptance gate.
        if fault == "missing_citation" and artifact.items:
            artifact.items[0].source_thread_id = ""
        elif fault == "auto_send" and artifact.items:
            artifact.items[0].sent = True
        elif fault == "empty_draft" and artifact.items:
            artifact.items[0].body = ""

        report = acceptance_suite(artifact, plan, emails)
        # Human review is reachable only when every acceptance check passes.
        ready_for_owner = report.all_pass
        return {
            "plan": plan,
            "artifact": artifact,
            "report": report,
            "ready_for_owner_review": ready_for_owner,
        }

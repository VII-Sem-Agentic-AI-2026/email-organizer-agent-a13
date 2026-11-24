from dataclasses import dataclass
from agents import DraftAgent, ValidationAgent, RepairAgent

@dataclass
class RunResult:
    drafts: list
    issues: list
    diagnosis_log: list
    passed: bool
    attempts: int

class ResilientEmailRuntime:
    def __init__(self, max_attempts=2):
        if max_attempts < 0:
            raise ValueError("max_attempts cannot be negative")
        self.max_attempts = max_attempts
        self.drafter = DraftAgent()
        self.validator = ValidationAgent()
        self.repairer = RepairAgent()

    def run(self, threads, injected_faults=None):
        injected_faults = injected_faults or {}
        by_id = {t.thread_id: t for t in threads}
        drafts = [self.drafter.create(t) for t in threads]

        # Failure injection is for testing the recovery path only.
        for draft in drafts:
            fault = injected_faults.get(draft.thread_id, {})
            if fault.get("wrong_citation"):
                draft.cited_thread_id = "wrong-thread"
            if fault.get("unauthorized_send"):
                draft.send_requested = True

        diagnosis_log = []
        attempts = 0
        issues = self.validator.validate(drafts)

        while issues and attempts < self.max_attempts:
            attempts += 1
            diagnosis_log.append(
                f"Attempt {attempts}: found {len(issues)} issue(s); repairing only reported fields."
            )
            for issue in issues:
                thread = by_id[issue.thread_id]
                draft = next(d for d in drafts if d.thread_id == issue.thread_id)
                self.repairer.repair(draft, issue, thread)
                diagnosis_log.append(
                    f"{issue.thread_id}: {issue.field} — {issue.reason}"
                )
            issues = self.validator.validate(drafts)

        if issues:
            diagnosis_log.append("Retry budget exhausted; output requires human review.")
        else:
            diagnosis_log.append("Validation passed; drafts remain drafts pending owner review.")

        return RunResult(drafts, issues, diagnosis_log, not issues, attempts)

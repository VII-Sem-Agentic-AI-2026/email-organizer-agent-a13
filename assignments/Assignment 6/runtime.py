from models import RunState
from audit import AuditLog
from checkpoint import CheckpointStore

class BudgetExceeded(RuntimeError):
    pass

class ApprovalRequired(RuntimeError):
    pass

class RuntimeController:
    def __init__(self, budget: int, audit: AuditLog, checkpoints: CheckpointStore):
        if budget < 1:
            raise ValueError("Budget must be at least 1.")
        self.budget = budget
        self.audit = audit
        self.checkpoints = checkpoints

    def run(self, steps, state: RunState, approved_actions=None):
        approved_actions = set(approved_actions or [])
        completed_this_run = 0

        print(f"\n[RUNTIME] Starting run: {state.run_id}")
        print(f"[RUNTIME] Step budget: {self.budget}")
        print(f"[RUNTIME] Resuming from step: {state.next_step + 1}")

        while state.next_step < len(steps):
            if completed_this_run >= self.budget:
                state.status = "PAUSED_BUDGET"
                self.checkpoints.save(state)
                print("[BUDGET] Limit reached. Saving checkpoint.")
                return state

            step = steps[state.next_step]

            print(f"\n[STEP {state.next_step + 1}] {step.intent}")
            print(f"[ACTION] {step.action_name}")
            print(f"[INPUT] {step.inputs}")

            if step.risky and step.action_name not in approved_actions:
                state.status = "WAITING_FOR_APPROVAL"
                self.audit.record(
                    run_id=state.run_id,
                    step_id=step.step_id,
                    intent=step.intent,
                    action=step.action_name,
                    inputs=step.inputs,
                    output={"message": "Approval required"},
                    status="BLOCKED"
                )
                self.checkpoints.save(state)
                print("[GATE] Risky action blocked. Approval required.")
                print("[CHECKPOINT] Waiting state saved.")
                raise ApprovalRequired(
                    f"Approval required before risky action: {step.action_name}"
                )

            try:
                print("[RUNTIME] Executing action...")
                output = step.action(step.inputs)
                print(f"[OUTPUT] {output}")

                self.audit.record(
                    run_id=state.run_id,
                    step_id=step.step_id,
                    intent=step.intent,
                    action=step.action_name,
                    inputs=step.inputs,
                    output=output,
                    status="COMPLETED"
                )
                print("[AUDIT] Action and input/output recorded.")

                state.outputs.append({
                    "step_id": step.step_id,
                    "action": step.action_name,
                    "output": output,
                })
                state.next_step += 1
                state.status = "RUNNING"

                self.checkpoints.save(state)
                print(f"[CHECKPOINT] Saved. Next step: {state.next_step + 1}")

                completed_this_run += 1

            except Exception as exc:
                state.status = "FAILED"
                self.audit.record(
                    run_id=state.run_id,
                    step_id=step.step_id,
                    intent=step.intent,
                    action=step.action_name,
                    inputs=step.inputs,
                    output={"error": str(exc)},
                    status="FAILED"
                )
                self.checkpoints.save(state)
                raise

        state.status = "COMPLETED"
        self.checkpoints.save(state)
        print("\n[RUNTIME] All steps completed.")
        return state

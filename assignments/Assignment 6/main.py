from pathlib import Path
from agent import build_steps, new_run_state
from audit import AuditLog
from checkpoint import CheckpointStore
from runtime import RuntimeController, ApprovalRequired

DATA_DIR = Path("runtime_data")

def main():
    audit = AuditLog(DATA_DIR / "audit.json")
    checkpoints = CheckpointStore(DATA_DIR / "checkpoint.json")
    runtime = RuntimeController(
        budget=3, audit=audit, checkpoints=checkpoints
    )
    steps = build_steps()
    state = new_run_state()

    print("\\nLAB 6 — CONTROLLED AGENT RUNTIME")
    print("=" * 44)
    print("Running first three safe steps with a budget of 3...")
    state = runtime.run(steps, state)
    print("Status:", state.status)
    print("Completed steps:", state.next_step)
    print("Checkpoint saved:", checkpoints.path)

    print("\\nResuming from the saved checkpoint...")
    state = checkpoints.load()
    try:
        runtime.run(steps, state)
    except ApprovalRequired as exc:
        print("Safety gate:", exc)
        print("The publish step was not executed.")

    print("\\nApproving the simulated publish step for this demo...")
    state = checkpoints.load()
    state = runtime.run(
        steps, state, approved_actions={"publish_draft"}
    )
    print("Final status:", state.status)
    print("Audit entries:", len(audit.entries))
    print("Audit file:", audit.path)
    print("Note: publish is simulated; no real email is sent.")

if __name__ == "__main__":
    main()

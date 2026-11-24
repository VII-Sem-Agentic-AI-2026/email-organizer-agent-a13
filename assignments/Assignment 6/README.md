# Assignment 6 — Runtime: Skills, Tools, Memory and Audit

## Aim
Run the Email Organizer workflow inside a controlled runtime with budgets, approval gates, audit logging and checkpoints.

## What is implemented
- Reusable plan/format skills from the earlier lab progression.
- Local mock tools for inbox reading, context retrieval and draft preparation.
- A runtime controller that limits the number of steps per run.
- A human approval gate for the risky `publish_draft` action.
- Audit records containing intent, action, inputs, output and status.
- Checkpoint saved after every completed step.
- Resume from the saved `next_step` after a paused run.
- A simulated publish action only; no email is sent.

## Run on Windows
```powershell
py -3.11 main.py
```

Run tests:
```powershell
py -3.11 -m unittest discover -s tests -v
```

No external packages, credentials or network access are required.

## Runtime flow
```text
Agent steps
    |
    v
Runtime Controller
    |
    +--> Check step budget
    +--> Check approval gate for risky action
    +--> Execute local tool
    +--> Audit intent, action, inputs and output
    +--> Save checkpoint
    |
    v
Completed / Paused / Waiting for approval
```

## Files created when the demo runs
`runtime_data/audit.json` stores the audit trail.
`runtime_data/checkpoint.json` stores the latest run state.

These are local demo files and can be deleted to reset the demo.

## Important notes
- The `publish_draft` tool is deliberately simulated and never contacts Gmail.
- Approval is passed explicitly to the runtime for this demo; no real human approval service is connected.
- The checkpoint stores the run position and completed outputs, allowing the workflow to resume at the next step.

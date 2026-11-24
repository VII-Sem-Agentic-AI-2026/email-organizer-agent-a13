# Assignment 11 — SDLC Factory: Spec → Tested Output

## Aim
Treat the locked plan as a specification and the triaged inbox with draft replies as a build artifact that must pass an automated acceptance suite before mailbox-owner review.

## What this lab demonstrates
- A locked plan defines required workflow steps, allowed priorities, thread-grounding, and no-auto-send rules.
- A build pipeline creates a triaged inbox with draft replies.
- An acceptance suite checks coverage, plan compliance, priorities, source-thread citations, draft content, and send safety.
- The factory marks an artifact ready for owner review only when every check passes.
- Failure injection demonstrates that invalid artifacts are blocked.

## Project structure
- `models.py` — plan, email, artifact, and acceptance report models.
- `pipeline.py` — builds the triaged inbox and draft replies.
- `acceptance.py` — automated acceptance checks.
- `factory.py` — coordinates build, test, and review gate.
- `main.py` — executable demonstration.
- `tests/` — acceptance and failure-gate tests.

## Run
Python 3.10 or newer is recommended. No external packages are required.

```bash
python main.py
```

## Test
```bash
python -m unittest discover -s tests -v
```

## Safety
This is a local mock implementation. It does not connect to Gmail, send messages, or modify calendars. Passing the acceptance suite only makes the drafts eligible for mailbox-owner review; it does not approve or publish them.

## Lab 11 alignment
The build command takes a locked plan, creates the triaged inbox with draft replies, runs the acceptance suite, and gates progression to human review on `report.all_pass`. A failed acceptance check blocks the artifact.

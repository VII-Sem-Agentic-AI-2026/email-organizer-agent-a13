# Assignment 10 — Ops Resilience: Validate, Diagnose and Fix

## Aim
Make the Email Organizer recover from validation failures by diagnosing the exact failing constraint and repairing only the affected part.

## What this lab demonstrates
- A validation agent checks that no email is sent without owner approval.
- Every draft must cite its own source email thread.
- A diagnosis log records the failed constraint.
- The repair agent changes only the field identified by validation.
- A bounded retry budget prevents endless repair loops.
- If the budget is exhausted, the run is escalated for human review.

## Project structure
- `models.py` — typed data models.
- `agents.py` — draft, validation and targeted repair agents.
- `runtime.py` — bounded validation/repair loop.
- `main.py` — runnable demo with injected faults.
- `tests/` — failure-injection and recovery tests.

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
This is a local mock demonstration. It does not connect to Gmail, send messages, or modify a calendar. All outputs remain drafts pending mailbox-owner approval.

## Lab 10 alignment
The lab uses a validation report, diagnoses the exact failing field, repairs only the offending part, and stops after the configured retry budget. This follows the worklet's Lab 10 requirement: injected faults must be detected and fixed within the retry budget; failed runs are not silently advanced.

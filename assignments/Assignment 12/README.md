# Assignment 12 — Safety & Governance: Approval, Evaluation, Rollback

## Aim
Add confidentiality, role-based approval, evaluation metrics, versioning, and rollback to the Email Organizer workflow.

## What this lab demonstrates
- Draft and approved/published states.
- Role-based access: mailbox owner, reviewer, and guest.
- Confidentiality controls for private drafts.
- Only the mailbox owner can edit, approve, publish, or roll back.
- Publishing is blocked until owner approval.
- Each publication is stored as a version.
- Owner can restore a previous published version.
- Audit events and evaluation metrics record system actions and rejected attempts.

## Project structure
- `models.py` — actors, draft package, states, audit events, metrics.
- `governance.py` — access control, approval, publishing, versioning, rollback, audit, and metrics.
- `main.py` — runnable demonstration.
- `tests/` — governance and rollback tests.

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
This is a local mock governance demonstration. It does not connect to Gmail or publish/send real email. "Publish" means storing an approved package in the local version store.

## Lab 12 alignment
The mailbox owner approval gate is a hard stop; access control and confidentiality are enforced; evaluation metrics and version history are recorded; rollback restores a previous version. Confidentiality and rollback are treated as required controls, not optional extras.

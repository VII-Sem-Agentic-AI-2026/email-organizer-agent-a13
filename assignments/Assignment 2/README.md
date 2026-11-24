# Assignment 2 — Tool-Using Email Agent

## Aim
Build an agent that retrieves email and contact information through typed tools, then computes and validates results from the retrieved data.

## Tools implemented
1. `read_inbox()` — retrieves typed email records.
2. `read_thread(thread_id)` — retrieves the messages in an email thread.
3. `lookup_contact(email_address)` — retrieves contact category and previous replies.
4. `compute_and_check(email)` — checks sender details, calculates priority and optionally calculates days until a deadline.

## Project flow
`Coordinator → Inbox tool → Thread tool → Contact tool → Compute/check tool → Verified output`

The agent does not assume sender category or priority in its prompt. It obtains those details through the tools.

## Run on Windows
Open PowerShell in this folder and run:

```powershell
py -3.11 main.py
```

Run tests:

```powershell
py -3.11 -m unittest discover -s tests -v
```

No third-party packages are required.

## Important
This assignment uses local sample data so it can run safely without Gmail credentials. It does not access a real mailbox or send email. The main project already contains `tools.py`, `connector.py`, and `gmail_connector.py`; this assignment demonstrates the same tool-using design with explicit typed inputs, outputs, checks, and tests. A real Gmail adapter can be connected later without changing the agent's workflow.

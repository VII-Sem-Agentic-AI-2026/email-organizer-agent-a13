# Assignment 7 — Agentic Node Graph: Full Email Pipeline

## Aim
Connect the Email Organizer's specialist agents into one executable graph with shared state, validation branching, a bounded regenerate loop and a mailbox-owner approval gate.

## Pipeline nodes
1. Ingestion & Classification Agent
2. Priority & Urgency Agent
3. Draft Reply Agent
4. Action-Item Extraction Agent
5. Follow-up / Reminder Agent
6. Calendar & Task Sync Agent
7. Validation
8. Regenerate Draft (bounded back-edge)
9. Assemble Triaged Inbox
10. Mailbox Owner Review Gate
11. Simulated Publish (only after approval)

## Graph flow
```text
Coordinator
    |
Ingestion & Classification
    |
Priority & Urgency
    |
Draft Reply
    |
Action-Item Extraction
    |
Follow-up / Reminder
    |
Calendar & Task Sync
    |
Validation
   / \\
 fail  pass
  |     |
Regenerate  Assemble
  |          |
  +-> Validate
             |
      Owner Review Gate
          /       \\
      reject      approve
                    |
             Simulated Publish
```

The validation retry count is bounded (default: 2). If validation still fails, the run is escalated instead of looping forever.

## Run on Windows
```powershell
py -3.11 main.py
```

To simulate mailbox-owner approval and the final non-sending publish step:
```powershell
py -3.11 main.py --approve-demo
```

Run tests:
```powershell
py -3.11 -m unittest discover -s tests -v
```

No external packages or credentials are required.

## Output
The demo prints the triaged inbox, priorities, draft replies, action items, meeting proposals and graph trace. It also writes `lab7_output.json`.

## Safety and scope
- The graph uses local sample emails; no Gmail account is accessed.
- Drafts remain drafts unless the owner approval flag is explicitly supplied.
- Publish is simulated and never sends an actual email.
- Meeting times are not confirmed; the node only creates a proposal requiring faculty confirmation.
- Action items remain pending until a task owner confirms them.
- This is a standalone executable graph demonstrating the Lab 7 structure; it does not replace the main project's LangGraph implementation.

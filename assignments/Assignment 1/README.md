# Assignment 1 — Agent vs Chatbot

## Objective
Demonstrate an agent loop for the Email Organizer Agent. The coordinator clarifies a request, creates a plan, presents it, observes user feedback, and revises the plan.

## Concept
A basic chatbot usually gives a one-shot response. This program follows a multi-step loop:

1. **Clarify** — collect folders, priority rules and desired output.
2. **Plan** — prepare an inbox-organization workflow.
3. **Act** — display the proposed plan.
4. **Observe** — collect user feedback.
5. **Revise** — update the plan using that feedback.

## Requirements
- Python 3.10 or later
- No external packages required

## Run on Windows PowerShell
Open PowerShell in this folder and run:

```powershell
py -3.11 main.py
```

Or:

```powershell
python main.py
```

## Safety
This is Lab 1's standalone planner demonstration. It does not connect to Gmail, access a calendar, or send email. Sending remains outside this lab and requires explicit human approval in the complete project.

## Files
- `main.py` — executable coordinator loop.
- `README.md` — setup and explanation.

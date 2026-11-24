# Assignment 9 — Deep Research Agent (Email Organizer)

## Aim
Ground every candidate email output in the actual thread history and the mailbox owner's past replies, and reject unsupported content.

## What this lab demonstrates
- Local source readers for email thread history and the owner's prior replies.
- A candidate-generation step with explicit claims.
- A grounding step that checks each claim against the available source messages.
- An evidence record for every candidate and a consolidated evidence table.
- Rejection of candidates with unsupported claims or no in-scope source.

## Project structure
- `sources.py` — mock thread history and owner past replies.
- `models.py` — typed source, candidate, and evidence records.
- `grounding.py` — lexical source matching and evidence construction.
- `agent.py` — candidate generation and research/grounding workflow.
- `main.py` — runnable demonstration.
- `tests/test_grounding.py` — automated tests.

## Run
Python 3.10 or later; no third-party packages required.

```bash
python main.py
```

## Test
```bash
python -m unittest discover -s tests -v
```

## Important notes
This is a self-contained teaching demo using local sample messages, not a live Gmail research system. Matching uses transparent keyword overlap as a lightweight grounding approximation; it is not semantic embedding search or an LLM fact-checker. A real deployment should use exact message/thread identifiers and stronger claim-to-evidence verification. No email is sent.

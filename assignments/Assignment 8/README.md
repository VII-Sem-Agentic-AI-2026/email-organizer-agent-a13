# Assignment 8 — Parallel Swarm (Email Organizer)

## Objective
Process multiple email threads concurrently, generate worker alternatives for each thread, and merge them by strict alignment with a locked plan.

## What is implemented
- A locked plan defines required output fields and priority rules.
- `ParallelSwarm` uses Python's `ThreadPoolExecutor` to fan out email-thread work concurrently.
- Two deterministic specialist workers create alternatives for each email.
- The merge selector chooses the candidate with the strongest required-field coverage and plan-alignment score.
- Fan-in preserves the original email order and verifies that every input thread has a merged result.

This is a self-contained teaching demo. Workers use deterministic local rules, not separate LLMs. It demonstrates the parallel orchestration pattern from Lab 8; it is not a replacement for the main project's runtime. No Gmail connection, real email sending, or calendar changes occur.

## Requirements
Python 3.10 or newer. No third-party packages required.

## Run
From this folder:

```bash
python main.py
```

## Test

```bash
python -m unittest discover -s tests -v
```

## Main files
- `models.py` — typed plan, email, candidate, and result models
- `workers.py` — parallel worker pool and fan-out
- `merge.py` — plan-alignment selector and fan-in
- `agent.py` — coordinator
- `main.py` — runnable sample
- `tests/test_swarm.py` — tests for completeness, selection, ordering, and empty input

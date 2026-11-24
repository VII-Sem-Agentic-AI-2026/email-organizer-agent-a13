# Coursework & Lab Assignments

This folder is dedicated to course lab assignments and coursework submissions.
| Lab | Concept | How this project demonstrates it |
|-----|---------|----------------------------------|
| Lab 1 | Agent vs Chatbot | Moves beyond simple Q&A by proactively proposing, refining, and executing a multi-step triage plan. |
| Lab 2 | Tool-Using Agent | Agents utilize strict interfaces (`GmailConnector`, `check_deadline`) to interact with the outside world. |
| Lab 3 | Skill Creation | Employs reusable formatting and reasoning skills applied across different email contexts. |
| Lab 4 | Memory & Retrieval | Maintains session state (draft queues) while grounding responses in long-term retrieved thread history. |
| Lab 5 | MCP-style Connector | Abstracts Gmail and Calendar APIs into modular connectors, allowing backend swaps without agent logic changes. |
| Lab 6 | Runtime | Manages the execution context, enforces approval gates, and logs state transitions. |
| Lab 7 | Agentic Node Graph | The pipeline is modeled as a DAG (`ingest` → `classify` → `draft` → `validate`), with back-edges for self-correction. |
| Lab 8 | Parallel Swarm | Utilizes `ThreadPoolExecutor` to process multiple incoming emails concurrently, dramatically reducing wall-clock time. |
| Lab 9 | Deep Research / Grounding | Interrogates the Gmail API for historical thread context to ensure drafts are factually anchored. |
| Lab 10 | Operational Resilience | Employs `_safe` wrapper functions and bounded retries to gracefully fallback if the Groq API experiences downtime. |
| Lab 11 | SDLC / Acceptance | Governed by explicit agent specifications and backed by automated test suites simulating the pipeline. |
| Lab 12 | Safety / Governance | Implements strict human-in-the-loop review queues, preventing autonomous sending and tracking audit histories. |
| Lab 13 | Discipline-Specific Agents | Splits complex reasoning into specialist sub-agents (e.g., `meeting_agent.py` parsing strict datetime schemas). |
| Lab 14 | Capstone Integration | Culminates in a unified Flask dashboard that brings the connectors, parallel swarm, governance, and specialist agents into a single product. |

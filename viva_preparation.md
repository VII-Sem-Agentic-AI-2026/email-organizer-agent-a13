# Email Organizer Agent — Viva Preparation Guide

This guide provides a verified, code-backed analysis of your project to help you confidently defend your implementation during the viva.

## 1. Verified Architecture Inventory

Based on a direct audit of your repository files, here are the **actual** counts and facts:

*   **LangGraph Nodes (7):** `ingest`, `classify`, `extract_actions`, `create_draft`, `ground`, `validate`, `regenerate`. (Found in `app/graph.py`).
*   **LangGraph Edges (8):** 7 standard edges connecting the nodes sequentially, plus 1 conditional edge (`validate` -> `end` OR `regenerate`).
*   **Independent LLM-powered Agents (1):** Only **one** module (`app/classifier.py`) actually calls an LLM (Groq). It handles two tasks: `classify_email` and `extract_action_items`.
*   **Deterministic "Agents" / Logic Blocks (3):** 
    *   `draft_agent.py`: Uses deterministic template matching (`response_library.py`), no LLM.
    *   `meeting_agent.py`: Uses keyword regex/matching, no LLM.
    *   `calendar_agent.py`: Uses standard Python datetime logic to calculate overlaps, no LLM.
*   **Connector Modules (3):** 
    *   `connector.py` (Base `EmailConnector` and `MockEmailConnector`)
    *   `gmail_connector.py` (Gmail API integration)
    *   `calendar_connector.py` (Calendar API integration)
*   **External Service Integrations (2):** Google Workspace (Gmail API) and Google Calendar API. Groq API for LLM inference.
*   **Implementation Style:** You implemented an **"MCP-style connector architecture"** (using a typed interface layer), NOT the official Model Context Protocol (no SDK, no JSON-RPC over stdio).

---

## 2. Complete Project Overview (Elevator Pitches)

**30-Second Introduction:**
"My project is an agentic AI Email Organizer that triages incoming emails. Unlike a traditional chatbot, it proactively fetches emails using the Gmail API, classifies them, extracts deadlines, and checks my calendar for meeting requests. It then prepares grounded draft replies using a LangGraph workflow and places them in a human-in-the-loop review queue so I have final approval before anything is sent."

**1-Minute Introduction:**
"The Email Organizer Agent is an agentic AI system designed to solve inbox overload. Traditional chatbots require you to copy-paste text and ask questions. My system is agentic because it independently polls Gmail, parses content using a Groq LLM, and orchestrates a multi-step workflow using LangGraph. The graph routes the email through specialized agents: it classifies the sender, extracts action items, detects meeting requests using the Calendar API, and drafts a response grounded in actual thread history. Finally, it uses a strict governance model—all drafts go to a Flask dashboard where I must explicitly approve them before they are sent via the Gmail API, ensuring complete safety."

**2-Minute Introduction:**
*(Combine the 1-minute pitch with architecture details)*
"The core architecture is built around LangGraph, defining a StateGraph with 7 nodes. An email flows from `ingest` to `classify` to `extract_actions` to `create_draft`. We use Groq's `openai/gpt-oss-20b` model to enforce strict Pydantic JSON outputs for priority and actions. A major challenge with AI is hallucination, so I implemented a `ground` node that pulls previous messages from the Gmail thread to provide factual context. If a draft lacks evidence or missing fields, the `validate` node triggers a conditional edge to `regenerate` the draft. The system is designed with a strict Human-In-The-Loop paradigm. Parallel processing is used via `ThreadPoolExecutor` in `swarm.py` to handle multiple emails simultaneously. The final outputs—categorized emails, extracted tasks, and proposed meeting slots—are rendered on a Flask dashboard for final faculty approval."

---

## 3. LangGraph Viva Questions

**Q: What is LangGraph and why did you use it?**
**A:** LangGraph is a library for building stateful, multi-actor applications with LLMs. I used it instead of sequential function calls because it allows for cyclic graphs—specifically, it lets me implement a `regenerate` loop. If an email classification or draft fails validation, the graph automatically routes it backward to be fixed before reaching the user.

**Q: Explain the graph architecture in `app/graph.py`.**
**A:** It uses a `StateGraph`. 
*   **State:** A `GraphState` dataclass holding emails, classifications, action items, drafts, and validation errors.
*   **Nodes (7):** `ingest`, `classify`, `extract_actions`, `create_draft`, `ground`, `validate`, `regenerate`.
*   **Conditional Edge:** From `validate`, it runs `route_after_validation`. If `validation_passed` is true or attempts >= 2, it routes to `END`. Otherwise, it routes to `regenerate`.
*   **Compile & Invoke:** `build_graph().compile()` turns the definition into an executable state machine, and `.invoke(initial_state)` runs it.

**Q: What happens if validation fails?**
**A:** The conditional edge routes the state to the `regenerate` node. The system clears the `validation_passed` flag, increments the `attempts` counter, and re-runs classification and drafting. Retries are bounded to a maximum of 2 attempts to prevent infinite loops.

---

## 4. Agent and Component Counts

**Q: How many agents does your project have?**
**A:** Conceptually, it's a multi-agent system, but structurally it relies on one core LLM component and several deterministic specialist agents. 
1. **LLM Component:** `classifier.py` acts as the AI intelligence, calling Groq to classify and extract tasks.
2. **Deterministic Specialists:** `calendar_agent.py` (computes slot overlaps), `meeting_agent.py` (detects meeting keywords), and `draft_agent.py` (matches standard templates). 
3. **Workflow Engine:** LangGraph acts as the coordinator.

**Q: What is the difference between an agent, a node, and a tool in your code?**
**A:** 
*   **Tool:** A pure Python function that interacts with the outside world (e.g., `read_inbox` in `tools.py`).
*   **Node:** A step in the LangGraph state machine (e.g., `classify_node`).
*   **Agent:** A component that encapsulates reasoning or domain logic (e.g., `calendar_agent.py` figuring out busy overlaps).

**Q: Does parallel processing (`swarm.py`) use multiple LLM agents?**
**A:** No. `swarm.py` uses `ThreadPoolExecutor` (concurrency) to process multiple emails at the same time. It's a fan-out/fan-in parallel worker pattern, not multiple distinct AI personas arguing with each other.

---

## 5. MCP and Connectors

**Q: Do you use the official Model Context Protocol (MCP)?**
**A:** No, my project implements an **"MCP-style connector architecture,"** as outlined in the labs. It uses a typed Python interface (`EmailConnector` in `connector.py`) to abstract the data sources. This allows me to easily swap between a `MockEmailConnector` for testing and the real `GmailConnector` without changing the core agent logic.

**Q: How does the Calendar integration work?**
**A:** `calendar_connector.py` uses the Google Calendar API to query the `freebusy` endpoint. It returns busy time blocks. `calendar_agent.py` then takes those blocks, checks standard working hours (9 AM - 5 PM), skips weekends, and proposes non-overlapping 30-minute slots.

---

## 6. LLMs and Prompting

**Q: Which LLM do you use and how?**
**A:** I use the Groq API, specifically configuring the model name `openai/gpt-oss-20b`. I prompt it to return strictly formatted JSON.

**Q: How do you enforce structured output?**
**A:** In the prompt, I provide the exact JSON structure and the allowed enum values (e.g., Priority must be Critical, High, Medium, or Low). After Groq returns the string, I parse it with `json.loads` and pass it to a **Pydantic model** (`EmailClassification`) which throws a validation error if the LLM hallucinates an invalid category.

**Q: What happens when the LLM request fails?**
**A:** I implemented operational resilience (`classify_email_safe`). If the Groq API times out or fails Pydantic validation, it falls back to deterministic heuristic Python logic (e.g., if the word "urgent" is in the subject, Priority = Critical).

---

## 7. Memory and Grounding

**Q: How is memory and grounding implemented?**
**A:** I have two forms of memory:
1. **Long-Term Synthetic Memory (`memory.py`):** Uses a simple list of `MemoryItem` objects and retrieves them based on naive tag/keyword matching.
2. **Real Thread Grounding (`thread_grounding.py`):** It looks at the incoming email's `threadId`, uses the Gmail API to fetch previous messages in that exact thread, and scores them for relevance based on word overlap. 

**Q: Do you use a Vector Database or Embeddings?**
**A:** No. The project uses deterministic token/word intersection for relevance scoring, which is lightweight and doesn't require an external vector database.

---

## 8. Governance and Safety

**Q: How do you prevent the AI from sending emails autonomously?**
**A:** The system operates strictly as decision-support. 
1. `graph.py` generates drafts and saves them to memory.
2. `governance.py` assigns them a state of `ApprovalState.DRAFT`.
3. The Flask dashboard displays them. The faculty member must click "Approve", changing the state to `APPROVED`.
4. In `gmail_sender.py`, there is a hardcoded check: `if review_item.state != ReviewState.APPROVED: raise PermissionError()`.

---

## 9. 14 Labs Mapping (Quick Reference)

*   **Lab 1 (Agent vs Chatbot):** Proactive inbox polling vs reactive chat.
*   **Lab 2 (Tool-using):** `tools.py` and `connector.py` wrap API calls.
*   **Lab 3 (Skills):** Reusable functions in `classifier.py`.
*   **Lab 4 (Memory):** `memory.py` state management.
*   **Lab 5 (MCP-style):** Abstract `EmailConnector` base class.
*   **Lab 6 (Runtime):** `coordinator.py` and execution state.
*   **Lab 7 (Agentic Graph):** LangGraph integration in `graph.py`.
*   **Lab 8 (Parallel Swarm):** `ThreadPoolExecutor` in `swarm.py`.
*   **Lab 9 (Deep Grounding):** Gmail thread retrieval in `thread_grounding.py`.
*   **Lab 10 (Resilience/Retry):** `_safe` wrapper fallbacks and LangGraph `regenerate` node.
*   **Lab 11 (Spec-driven):** Pydantic schemas validating output.
*   **Lab 12 (Governance):** `review_queue.py` and `ApprovalState`.
*   **Lab 13 (Specialists):** `calendar_agent.py` handling specific datetime logic.
*   **Lab 14 (Capstone):** `dashboard.py` tying it all together.

---

## 10. Top 15 Likely Examiner Questions (To practice)

1. How is your project different from a simple ChatGPT script?
2. Exactly how many nodes are in your LangGraph, and what do they do?
3. Walk me through what happens when `validation_passed` is False.
4. If your Groq API key expires right now, will the application crash?
5. You claim you have a Calendar Agent. Does it use AI?
6. How does your code guarantee that an email is never sent without permission?
7. Explain your implementation of the MCP (Model Context Protocol) architecture.
8. How does `swarm.py` improve performance?
9. What happens if I send an email in a brand new thread? Does grounding fail?
10. How do you force the LLM to return exactly the categories you want?
11. What is the role of Pydantic in this project?
12. Why did you use `ThreadPoolExecutor` instead of multiple LLM calls simultaneously?
13. Show me where the application stores its state.
14. Explain the difference between `draft_agent.py` and `classifier.py`.
15. What is the most significant limitation of your current implementation?

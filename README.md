# Agentic AI — Email Organizer Agent

An autonomous, multi-agent academic assistant that automates inbox triaging, priority-based action extraction, meeting scheduling via Google Calendar, and context-aware drafting with strict Human-in-the-Loop governance.

---

## Team Details

| Name | USN | Division |
|---|---|---|
| Mishty Dak | 01fe23bci006 | A Div |
| Diya Habib | 01fe23bci021 | A Div |
| Ananya Kadakol | 01fe23bci025 | A Div |
| Bhagyashri Jogin | 01fe23bci077 | A Div |

---

## 1. Problem Statement
Academic faculty and professionals face severe inbox overload from mixed incoming messages—ranging from routine student inquiries and administrative deadlines to urgent meeting requests. Manually triaging emails, extracting deadlines, resolving calendar conflicts, and drafting personalized replies is inefficient and prone to missed priorities. Existing chatbots lack autonomous tool execution, calendar awareness, and safe human-in-the-loop controls.

## 2. Objectives
- **Autonomous Triage:** Classify sender categories and detect urgency levels (`Critical`, `High`, `Medium`, `Low`).
- **Action Extraction:** Extract explicit actionable tasks, deadlines, and assignees.
- **Conflict-Free Scheduling:** Detect meeting requests, query Google Calendar for free/busy blocks, and propose available 30-minute slots.
- **Context-Aware Drafting:** Generate grounded, professional email replies using Groq LLM without hallucination.
- **Persistent Reminders:** Schedule SQLite-backed reminders and custom snooze intervals for unanswered high-priority emails.
- **Human-in-the-Loop (HITL) Governance:** Guarantee that no email is sent and no calendar event is created without explicit user approval.

## 3. Approach
- **Cyclic Workflow Engine:** Orchestrated via a **7-node LangGraph** state machine (`ingest` → `classify` → `extract_actions` → `create_draft` → `ground` → `validate` ⟲ `regenerate`).
- **Hybrid Multi-Agent Architecture:**
  - *Cognitive LLM Agents:* Powered by Groq (`openai/gpt-oss-20b`) with strict Pydantic schema validation.
  - *Deterministic Specialists:* Mathematical conflict calculation for calendar slots, regex parsing for meeting intent, and background SQLite scheduling.
- **MCP-Style Connector Layer:** Decoupled typed interfaces (`EmailConnector`, `GoogleCalendarConnector`) enabling seamless switching between live Google APIs and offline mock fixtures for automated testing.
- **Concurrent Ingestion Swarm:** Multi-threaded parallel worker (`ThreadPoolExecutor`) for high-throughput batch processing of emails.

## 4. Implementation
- **Backend:** Python 3.11, Flask REST API, LangGraph, Pydantic, SQLite.
- **External Integrations:**
  - **Groq API:** Fast LLM inference for classification, task extraction, and contextual drafting.
  - **Gmail API:** Live message ingestion, thread grounding, and RFC 2822 threaded replies (`In-Reply-To`, `References`, `threadId`).
  - **Google Calendar API:** Live FreeBusy querying and `events.insert` upon user approval.
- **Frontend Dashboard:** Responsive web interface with Triaged Inbox, Action Items, Meeting Approval with slot picker, Draft Review Queue with in-place editor, and Priority Reminder alerts.

## 5. Results
- **100% Test Suite Pass Rate:** All 15 automated integration tests pass offline using isolated mocks (`tests/test_enhanced_features.py`).
- **Zero Unauthorized Actions:** Strict approval barrier prevents unapproved emails or phantom calendar bookings.
- **Fault-Tolerant Resilience:** Multi-tier fallback to standard response templates if the LLM API is unreachable.
- **State Persistence:** Reminders survive application restarts via persistent SQLite storage.

---

## 6. Repository Structure

```
email-organizer/
├── assignments/            
└── project/                
    ├── app/                
    │   ├── static/        
    │   ├── templates/      
    │   ├── classifier.py   
    │   ├── draft_agent.py  
    │   ├── calendar_agent.py 
    │   ├── meeting_agent.py  
    │   ├── reminder_manager.py 
    │   ├── graph.py        
    │   ├── dashboard.py    
    │   └── ...
    ├── scripts/            
    ├── tests/              
    ├── .env.example        
    ├── requirements.txt    
    └── README.md           
```

---

## 7. Quickstart Guide

```bash
# 1. Navigate to project
cd project

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Add your GROQ_API_KEY to .env

# 4. Run automated test suite (100% offline)
pytest tests/test_enhanced_features.py -v

# 5. Launch the Dashboard
python app/dashboard.py
# Open http://127.0.0.1:5000 in your browser
```

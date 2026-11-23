# Agentic AI — Course Repository

This repository contains coursework submissions and the final Email Organizer Agent project.

## Team Details

| Name | USN | Division |
|---|---|---|
| Mishty Dak | 01fe23bci006 | `<A Div>` |
| Diya Habib | 01fe23bci021 | `<A Div>` |
| Ananya Kadakol | 01fe23bci025 | `<A Div>` |
| Bhagyashri Jogin | 01fe23bci077 | `<A Div>` |

---

## Repository Structure

```
├── assignments/            # Coursework and lab assignments
└── project/                # AI Email Organizer Agent (Main Project)
    ├── app/                # Core application (agents, connectors, Flask UI)
    ├── scripts/            # OAuth authentication and diagnostic tools
    ├── tests/              # Automated unit and integration tests
    ├── requirements.txt    # Python dependencies
    └── README.md           # Detailed project documentation
```

---

## Quickstart (Main Project)

To run the Email Organizer Agent:

```bash
# 1. Navigate to the project directory
cd project

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your GROQ_API_KEY

# 4. Run automated tests (offline)
pytest tests/test_enhanced_features.py -v

# 5. Launch dashboard
python app/dashboard.py
```
For full architecture details, refer to [`project/README.md`](project/README.md).

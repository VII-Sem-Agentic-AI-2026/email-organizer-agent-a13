# Assignment 3 — Skill Creation

## Aim
Create reusable, schema-typed planning and formatting skills for the Email Organizer Agent.

## Skills implemented
1. `plan_skill(inputs: PlanInputs) -> Plan`
   - Accepts structured request inputs.
   - Creates a plan with goal, steps, priority rules and constraints.
   - Returns a locked Plan object.

2. `format_triaged_skill(result: TriageResult, template: TemplateSpec) -> Document`
   - Accepts typed triage results and a template specification.
   - Produces a formatted triaged inbox with draft replies and an approval section.

## Agent flow
`Typed inputs → Planning skill → Locked Plan`
`Triage result + TemplateSpec → Formatting skill → Document`

## Acceptance demonstration
The same planning skill is called with two different cases (student emails and administration emails). The same formatting skill also renders different results using different template titles. No changes to the skill code are needed between cases.

## Run on Windows
```powershell
py -3.11 main.py
```

Run tests:
```powershell
py -3.11 -m unittest discover -s tests -v
```

No external packages, Gmail credentials or API keys are required. The sample triage record is local demonstration data. Nothing is sent.

## Project relationship
The main project already contains a basic `skills.py` utility. This assignment provides explicit typed input/output models, two callable reusable skills, an agent that invokes them, and tests demonstrating reuse across cases.

from models import Candidate, ResearchResult
from grounding import ground_candidate

def generate_candidates():
    # Candidate claims are deliberately explicit so the grounding step can verify each one.
    return [
        Candidate("T-101", "Project report deadline", "The report is due Friday, 28 November. Please share the completed draft and I can review its format.", [
            "The project report is due Friday 28 November",
            "The student has completed data collection",
            "The owner can review the format after receiving the completed draft",
        ]),
        Candidate("T-102", "Revised event schedule", "Please send the revised event schedule by Wednesday and include the confirmed timings. The event is planned for the department seminar hall.", [
            "The revised event schedule is requested by Wednesday",
            "The event is planned for the department seminar hall",
            "The owner asked for confirmed timings in the revised schedule",
        ]),
        Candidate("T-999", "Unsupported claim example", "The meeting is approved for Monday at 10 AM.", [
            "The meeting is approved for Monday at 10 AM",
        ]),
    ]

def run_research_agent() -> ResearchResult:
    grounded = [ground_candidate(c) for c in generate_candidates()]
    accepted = [g for g in grounded if g.evidence.in_scope]
    rejected = [g.candidate.unit_id for g in grounded if not g.evidence.in_scope]
    return ResearchResult(items=accepted, evidence_table=[g.evidence for g in grounded], rejected_unit_ids=rejected)

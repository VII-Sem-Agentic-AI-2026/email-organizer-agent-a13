from models import Candidate, EmailThread, LockedPlan, MergedEmail

def select_best(candidates: list[Candidate], plan: LockedPlan) -> Candidate:
    if not candidates:
        raise ValueError("No worker candidates to merge")
    # Strictly select by required-field coverage and plan alignment, not style.
    return max(candidates, key=lambda c: (c.alignment_score,
                                          sum(f in c.covered_fields for f in plan.required_fields),
                                          c.worker == "Triage Worker"))

def merge_results(emails: list[EmailThread], candidate_groups: list[list[Candidate]], plan: LockedPlan) -> list[MergedEmail]:
    if len(emails) != len(candidate_groups):
        raise ValueError("Fan-in must receive one candidate group for every input thread")
    merged = []
    for email, candidates in zip(emails, candidate_groups):
        best = select_best(candidates, plan)
        merged.append(MergedEmail(email.thread_id, email.sender, email.subject,
                                  best.priority, best.summary, best.draft_reply,
                                  best.worker, best.alignment_score))
    return merged

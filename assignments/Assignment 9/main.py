from agent import run_research_agent

def main():
    result = run_research_agent()
    print("EMAIL ORGANIZER — LAB 9: DEEP RESEARCH / GROUNDING")
    print("=" * 58)
    print(f"Grounded candidates accepted: {len(result.items)}")
    for item in result.items:
        print(f"\n[{item.candidate.unit_id}] {item.candidate.subject}")
        print("Draft:", item.candidate.draft)
        print("Evidence:", ", ".join(item.evidence.source_ids))
        for claim in item.evidence.supported_claims:
            print("  +", claim)
    print("\nEvidence table")
    for ev in result.evidence_table:
        status = "ACCEPTED" if ev.in_scope else "REJECTED"
        print(f"- {ev.unit_id}: {status}; sources={ev.source_ids}; unsupported={ev.unsupported_claims}")
    print("\nRejected candidates:", ", ".join(result.rejected_unit_ids) or "None")
    print("\nDemo only: local sample thread history and owner replies; no Gmail access or email sending.")

if __name__ == "__main__":
    main()

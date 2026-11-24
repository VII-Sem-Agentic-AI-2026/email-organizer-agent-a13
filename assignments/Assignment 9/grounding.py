import re
from models import Candidate, EvidenceRecord, GroundedCandidate
from sources import get_sources

STOP = {"the", "a", "an", "and", "or", "to", "of", "for", "is", "are", "was", "were", "be", "been", "on", "in", "at", "after", "before", "please", "you", "your", "i", "we", "it", "this", "that", "with", "from", "has", "have", "will", "can", "could", "would", "share", "send", "include"}

def tokens(text: str):
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if len(w) > 1 and w not in STOP}

def claim_supported(claim: str, source_texts, threshold: float = 0.30) -> bool:
    claim_words = tokens(claim)
    if not claim_words:
        return False
    for source in source_texts:
        source_words = tokens(source)
        if len(claim_words & source_words) / len(claim_words) >= threshold:
            return True
    return False

def ground_candidate(candidate: Candidate) -> GroundedCandidate:
    sources = get_sources(candidate.unit_id)
    source_texts = [s.text for s in sources]
    record = EvidenceRecord(unit_id=candidate.unit_id)
    for claim in candidate.claims:
        if claim_supported(claim, source_texts):
            record.supported_claims.append(claim)
        else:
            record.unsupported_claims.append(claim)
    record.source_ids = [s.source_id for s in sources if any(claim_supported(c, [s.text]) for c in candidate.claims)]
    record.in_scope = bool(sources) and bool(candidate.claims) and not record.unsupported_claims
    return GroundedCandidate(candidate=candidate, evidence=record)

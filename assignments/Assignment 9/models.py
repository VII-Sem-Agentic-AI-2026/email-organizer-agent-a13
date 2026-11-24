from dataclasses import dataclass, field
from typing import List

@dataclass(frozen=True)
class SourceMessage:
    source_id: str
    source_type: str  # thread_history or owner_past_reply
    text: str

@dataclass(frozen=True)
class Candidate:
    unit_id: str
    subject: str
    draft: str
    claims: List[str]

@dataclass
class EvidenceRecord:
    unit_id: str
    supported_claims: List[str] = field(default_factory=list)
    unsupported_claims: List[str] = field(default_factory=list)
    source_ids: List[str] = field(default_factory=list)
    in_scope: bool = False

@dataclass
class GroundedCandidate:
    candidate: Candidate
    evidence: EvidenceRecord

@dataclass
class ResearchResult:
    items: List[GroundedCandidate]
    evidence_table: List[EvidenceRecord]
    rejected_unit_ids: List[str]

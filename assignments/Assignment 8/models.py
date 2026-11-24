from dataclasses import dataclass, field

@dataclass(frozen=True)
class LockedPlan:
    required_fields: tuple[str, ...] = ("sender", "subject", "priority", "summary", "draft_reply")
    priority_rules: tuple[str, ...] = ("urgent deadlines first", "answer every email thread")
    max_workers: int = 4

@dataclass(frozen=True)
class EmailThread:
    thread_id: str
    sender: str
    subject: str
    body: str
    deadline: str = ""

@dataclass
class Candidate:
    thread_id: str
    worker: str
    priority: str
    summary: str
    draft_reply: str
    alignment_score: int
    covered_fields: tuple[str, ...] = field(default_factory=tuple)

@dataclass
class MergedEmail:
    thread_id: str
    sender: str
    subject: str
    priority: str
    summary: str
    draft_reply: str
    selected_worker: str
    alignment_score: int

@dataclass
class SwarmResult:
    processed_thread_ids: list[str]
    selected: list[MergedEmail]
    worker_count: int
    all_threads_processed: bool

from dataclasses import dataclass, field
from typing import List

@dataclass
class EmailThread:
    thread_id: str
    sender: str
    subject: str
    message: str

@dataclass
class Draft:
    thread_id: str
    body: str
    cited_thread_id: str = ""
    send_requested: bool = False
    approved: bool = False
    repair_history: List[str] = field(default_factory=list)

@dataclass
class ValidationIssue:
    thread_id: str
    field: str
    reason: str

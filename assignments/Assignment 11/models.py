from dataclasses import dataclass, field
from typing import List

@dataclass
class Email:
    thread_id: str
    sender: str
    subject: str
    message: str
    priority: str

@dataclass
class LockedPlan:
    required_steps: tuple = ("classify", "prioritize", "draft", "ground", "validate")
    allowed_priorities: tuple = ("HIGH", "NORMAL", "LOW")
    require_thread_citation: bool = True
    prohibit_auto_send: bool = True

@dataclass
class DraftReply:
    thread_id: str
    sender: str
    subject: str
    priority: str
    body: str
    source_thread_id: str
    sent: bool = False

@dataclass
class InboxArtifact:
    plan_steps: tuple
    items: List[DraftReply] = field(default_factory=list)

@dataclass
class Check:
    name: str
    passed: bool
    detail: str

@dataclass
class AcceptanceReport:
    checks: List[Check]

    @property
    def all_pass(self):
        return bool(self.checks) and all(c.passed for c in self.checks)

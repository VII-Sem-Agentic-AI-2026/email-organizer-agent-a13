from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List

class Status(str, Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    PUBLISHED = "published"

@dataclass
class Actor:
    user_id: str
    role: str

    @property
    def can_approve(self):
        return self.role == "mailbox_owner"

    @property
    def can_view_private(self):
        return self.role in {"mailbox_owner", "reviewer"}

@dataclass
class DraftPackage:
    package_id: str
    body: str
    status: Status = Status.DRAFT
    version: int = 0
    approved_by: str = ""
    edits: List[str] = field(default_factory=list)

@dataclass
class AuditEvent:
    action: str
    actor: str
    version: int
    detail: str

@dataclass
class Metrics:
    approvals: int = 0
    publications: int = 0
    rollbacks: int = 0
    rejected_actions: int = 0

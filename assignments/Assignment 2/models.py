from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Email:
    message_id: str
    thread_id: str
    sender: str
    subject: str
    body: str

@dataclass
class Contact:
    email: str
    name: str
    category: str
    previous_replies: list[str] = field(default_factory=list)

@dataclass
class EmailCheck:
    message_id: str
    sender_known: bool
    sender_category: str
    priority: str
    deadline_days: Optional[int]
    valid: bool
    reasons: list[str] = field(default_factory=list)

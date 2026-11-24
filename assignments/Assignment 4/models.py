from dataclasses import dataclass, field
from typing import Any

@dataclass
class MemoryItem:
    item_id: str
    text: str
    tags: list[str] = field(default_factory=list)
    source: str = "email_history"
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class RunState:
    """Short-term state for the current execution; not part of long-term memory."""
    current_draft: str = ""
    current_email_id: str = ""
    notes: list[str] = field(default_factory=list)

@dataclass
class RetrievalHit:
    item: MemoryItem
    score: float
    matched_tags: list[str] = field(default_factory=list)

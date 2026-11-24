from dataclasses import dataclass, field
from typing import Any

@dataclass
class GraphState:
    run_id: str
    inbox: list[dict[str, Any]] = field(default_factory=list)
    triaged: list[dict[str, Any]] = field(default_factory=list)
    action_items: list[dict[str, Any]] = field(default_factory=list)
    follow_ups: list[dict[str, Any]] = field(default_factory=list)
    meeting_proposals: list[dict[str, Any]] = field(default_factory=list)
    validation_errors: list[str] = field(default_factory=list)
    validation_passed: bool = False
    attempts: int = 0
    max_attempts: int = 2
    assembled_report: dict[str, Any] | None = None
    review_status: str = "PENDING"
    publish_status: str = "NOT_PUBLISHED"
    trace: list[str] = field(default_factory=list)

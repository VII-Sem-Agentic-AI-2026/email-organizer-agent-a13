from dataclasses import dataclass, field
from typing import Any, Callable

@dataclass
class AgentStep:
    step_id: str
    intent: str
    action_name: str
    inputs: dict[str, Any]
    action: Callable[[dict[str, Any]], Any]
    risky: bool = False

@dataclass
class RunState:
    run_id: str
    next_step: int = 0
    outputs: list[dict[str, Any]] = field(default_factory=list)
    status: str = "RUNNING"

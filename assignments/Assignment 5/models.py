from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class ConnectorRequest:
    source: str
    operation: str
    token: str

@dataclass
class ConnectorResponse:
    source: str
    records: list[dict[str, Any]]
    count: int

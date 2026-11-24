import json
from pathlib import Path
from dataclasses import asdict
from models import RunState

class CheckpointStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def save(self, state: RunState):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(asdict(state), indent=2), encoding="utf-8")

    def load(self) -> RunState:
        if not self.path.exists():
            raise FileNotFoundError(self.path)
        data = json.loads(self.path.read_text(encoding="utf-8"))
        return RunState(**data)

    def clear(self):
        if self.path.exists():
            self.path.unlink()

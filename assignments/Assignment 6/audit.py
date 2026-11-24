import json
from pathlib import Path
from datetime import datetime, timezone

class AuditLog:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.entries = []
        if self.path.exists():
            self.entries = json.loads(self.path.read_text(encoding="utf-8"))

    def record(self, *, run_id, step_id, intent, action, inputs, output, status):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "run_id": run_id,
            "step_id": step_id,
            "intent": intent,
            "action": action,
            "inputs": inputs,
            "output": output,
            "status": status,
        }
        self.entries.append(entry)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self.entries, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        return entry

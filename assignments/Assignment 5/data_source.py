from abc import ABC, abstractmethod
from typing import Any

class DataSource(ABC):
    """Replaceable backend contract. Agents never use this directly."""

    @abstractmethod
    def read(self, source_name: str) -> list[dict[str, Any]]:
        raise NotImplementedError

class MockDataSource(DataSource):
    def __init__(self):
        self.data = {
            "inbox_threads": [
                {"id": "E101", "thread_id": "T10", "sender": "student@example.com",
                 "subject": "Project submission extension", "body": "May I submit the project on Friday?",
                 "tags": ["student", "project", "extension"]},
                {"id": "E102", "thread_id": "T11", "sender": "office@example.com",
                 "subject": "Department report deadline", "body": "Please submit the report by Thursday.",
                 "tags": ["admin", "report", "deadline"]}
            ],
            "contacts_replies": [
                {"email": "student@example.com", "name": "Asha", "relationship": "student",
                 "prior_reply": "Please share your reason and proposed submission date."},
                {"email": "office@example.com", "name": "Department Office", "relationship": "admin",
                 "prior_reply": "The department report format is attached."}
            ],
            "calendar_tasks": [
                {"id": "C01", "type": "calendar_event", "title": "Faculty meeting",
                 "date": "2026-11-25", "time": "11:00"},
                {"id": "K01", "type": "task", "title": "Review project submissions",
                 "due": "2026-11-27", "status": "pending"}
            ]
        }

    def read(self, source_name: str) -> list[dict[str, Any]]:
        if source_name not in self.data:
            raise KeyError(f"Unknown data source: {source_name}")
        # Return copies so callers cannot mutate the backend's records.
        return [dict(row) for row in self.data[source_name]]

class AlternateMockDataSource(MockDataSource):
    """Second backend used to prove that the connector can swap data sources."""
    def __init__(self):
        super().__init__()
        self.data["inbox_threads"] = [
            {"id": "E201", "thread_id": "T20", "sender": "newstudent@example.com",
             "subject": "Lab record clarification", "body": "Could you clarify the lab record format?",
             "tags": ["student", "lab"]}
        ]

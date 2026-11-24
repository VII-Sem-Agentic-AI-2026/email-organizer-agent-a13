from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class Email:
    email_id: str
    sender: str
    subject: str
    body: str
    thread_id: str
    received_date: str
    category: str = "unknown"


@dataclass
class Contact:
    email: str
    name: str
    category: str


@dataclass
class PriorReply:
    contact_email: str
    subject: str
    reply: str


@dataclass
class ToolResult:
    success: bool
    data: object
    source: str
    message: str = ""


class EmailTools:
    """Typed tools used by the Email Organizer Agent."""

    def __init__(self):
        self.inbox = [
            Email(
                "E001", "student@college.edu",
                "Assignment deadline extension",
                "Could I get an extension? The deadline is 28 November 2026.",
                "T001", "2026-11-24", "student"
            ),
            Email(
                "E002", "admin@college.edu",
                "Faculty meeting",
                "Please confirm availability for the faculty meeting.",
                "T002", "2026-11-24", "admin"
            ),
            Email(
                "E003", "research@college.edu",
                "Research collaboration",
                "Would you be interested in a research collaboration?",
                "T003", "2026-11-24", "collaborator"
            )
        ]

        self.threads = {
            "T001": [
                {"sender": "student@college.edu",
                 "message": "Could I get an extension?"},
                {"sender": "faculty@college.edu",
                 "message": "Please share the reason for your request."}
            ],
            "T002": [
                {"sender": "admin@college.edu",
                 "message": "Please confirm availability for the meeting."}
            ],
            "T003": [
                {"sender": "research@college.edu",
                 "message": "Would you be interested in collaboration?"}
            ]
        }

        self.contacts = [
            Contact("student@college.edu", "Student A", "student"),
            Contact("admin@college.edu", "College Admin", "admin"),
            Contact("research@college.edu", "Research Team", "collaborator")
        ]

        self.prior_replies = [
            PriorReply(
                "student@college.edu",
                "Assignment query",
                "Please refer to the assignment instructions and contact me if you need clarification."
            ),
            PriorReply(
                "admin@college.edu",
                "Meeting",
                "Thank you for the update. I will review my schedule."
            )
        ]

    def read_inbox(self) -> ToolResult:
        return ToolResult(True, self.inbox, "mock_inbox")

    def read_thread(self, thread_id: str) -> ToolResult:
        if thread_id not in self.threads:
            return ToolResult(False, None, "mock_threads", "Thread not found")
        return ToolResult(True, self.threads[thread_id], "mock_threads")

    def read_contacts(self) -> ToolResult:
        return ToolResult(True, self.contacts, "mock_contacts")

    def read_prior_replies(self, contact_email: str) -> ToolResult:
        matches = [
            reply for reply in self.prior_replies
            if reply.contact_email.lower() == contact_email.lower()
        ]
        return ToolResult(True, matches, "mock_prior_replies")

    def calculate_days_until(self, deadline: str) -> ToolResult:
        try:
            target = date.fromisoformat(deadline)
            days = (target - date.today()).days
            return ToolResult(True, days, "date_calculator")
        except ValueError:
            return ToolResult(False, None, "date_calculator", "Invalid date")

    def validate_email(self, email: Email) -> ToolResult:
        valid = bool(
            email.email_id
            and email.sender
            and "@" in email.sender
            and email.subject
            and email.thread_id
        )
        return ToolResult(
            valid, email, "email_validator",
            "" if valid else "Email data is incomplete or invalid"
        )



from dataclasses import dataclass, field

@dataclass
class PlanInputs:
    request: str
    folders: list[str] = field(default_factory=list)
    priority_rules: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)

@dataclass(frozen=True)
class Plan:
    goal: str
    steps: tuple[str, ...]
    constraints: tuple[str, ...]
    priority_rules: tuple[str, ...]
    locked: bool = True

@dataclass
class TriagedEmail:
    sender: str
    subject: str
    priority: str
    category: str
    next_action: str
    draft_reply: str = ""

@dataclass
class TriageResult:
    title: str
    emails: list[TriagedEmail] = field(default_factory=list)

@dataclass
class TemplateSpec:
    title: str = "Email Triage Report"
    include_drafts: bool = True
    include_rules: bool = True
    owner_label: str = "Mailbox Owner"

@dataclass(frozen=True)
class Document:
    title: str
    sections: tuple[str, ...]
    content: str

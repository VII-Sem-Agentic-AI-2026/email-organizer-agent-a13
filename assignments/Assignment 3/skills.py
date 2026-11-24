from dataclasses import dataclass, field
from typing import List


@dataclass
class PlanInput:
    case_name: str
    request: str
    folders: List[str]
    priority_rules: List[str]


@dataclass
class Plan:
    case_name: str
    goal: str
    steps: List[str]
    constraints: List[str]
    locked: bool = False


@dataclass
class TriagedEmail:
    sender: str
    category: str
    subject: str
    priority: str
    draft_reply: str
    status: str = "Awaiting owner approval"


@dataclass
class TriageResult:
    case_name: str
    emails: List[TriagedEmail] = field(default_factory=list)


@dataclass
class TemplateSpec:
    title: str
    include_drafts: bool = True
    include_priority: bool = True


@dataclass
class Document:
    title: str
    content: str


class PlanBlueprintSkill:
    """Reusable typed skill for generating a locked email organization plan."""

    def run(self, inputs: PlanInput) -> Plan:
        if not inputs.case_name or not inputs.request:
            raise ValueError("Case name and request are required.")

        steps = [
            f"Read emails from {', '.join(inputs.folders)}",
            "Classify emails by sender category and content type",
            f"Prioritize using {', '.join(inputs.priority_rules)}",
            "Extract tasks, deadlines and commitments",
            "Identify meeting requests",
            "Prepare draft replies",
            "Submit drafts for mailbox-owner review"
        ]

        return Plan(
            case_name=inputs.case_name,
            goal=inputs.request,
            steps=steps,
            constraints=[
                "Never send without mailbox-owner approval",
                "Never confirm meetings without approval",
                "Never mark tasks complete without confirmation"
            ],
            locked=True
        )


class FormatTriagedSkill:
    """Reusable typed skill for formatting triaged inbox results."""

    def run(self, result: TriageResult, template: TemplateSpec) -> Document:
        lines = [
            template.title,
            f"Case: {result.case_name}",
            "=" * 50
        ]

        if not result.emails:
            lines.append("No emails available.")

        for index, email in enumerate(result.emails, 1):
            lines.extend([
                f"\nEmail {index}: {email.subject}",
                f"Sender: {email.sender}",
                f"Category: {email.category}"
            ])

            if template.include_priority:
                lines.append(f"Priority: {email.priority}")

            if template.include_drafts:
                lines.append(f"Draft reply: {email.draft_reply}")

            lines.append(f"Status: {email.status}")

        lines.extend([
            "\nApproval rule: Mailbox-owner approval is required before sending."
        ])

        return Document(
            title=template.title,
            content="\n".join(lines)
        )

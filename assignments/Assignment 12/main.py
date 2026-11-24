from models import Actor, DraftPackage
from governance import GovernanceManager, GovernanceError

def main():
    owner = Actor("faculty-owner", "mailbox_owner")
    reviewer = Actor("faculty-reviewer", "reviewer")
    guest = Actor("guest-user", "guest")
    gov = GovernanceManager()

    draft = DraftPackage("PKG-001",
        "Draft reply: Thank you for your email. I will review your request.")

    print("EMAIL ORGANIZER — SAFETY & GOVERNANCE")
    print("=" * 46)

    try:
        gov.view(draft, guest)
    except GovernanceError as exc:
        print("Confidentiality control:", exc)

    gov.view(draft, reviewer)
    gov.edit(draft, owner,
        "Revised draft: Thank you for your email. I have noted your request.")
    try:
        gov.publish(draft, reviewer)
    except GovernanceError as exc:
        print("Approval gate:", exc)

    gov.approve(draft, owner)
    published = gov.publish(draft, owner)
    print(f"Published version: {published.version} ({published.status.value})")

    # Create a second approved version to demonstrate restoring v1.
    second = DraftPackage("PKG-001", "Second version of the approved reply.")
    gov.approve(second, owner)
    gov.publish(second, owner)
    print("Current version:", gov.current_version)

    restored = gov.rollback(1, owner)
    print(f"After rollback: version {restored.version} — {restored.body}")
    print("\\nEvaluation metrics:")
    for key, value in gov.evaluation_report().items():
        print(f"- {key}: {value}")
    print("\\nAudit trail:")
    for event in gov.audit:
        print(f"- {event.action} | {event.actor} | v{event.version} | {event.detail}")

if __name__ == "__main__":
    main()

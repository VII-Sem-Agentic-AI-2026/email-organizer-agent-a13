from copy import deepcopy
from models import Status, AuditEvent, Metrics

class GovernanceError(PermissionError):
    pass

class GovernanceManager:
    def __init__(self):
        self.versions = {}
        self.current_version = 0
        self.audit = []
        self.metrics = Metrics()

    def _log(self, action, actor, version, detail):
        self.audit.append(AuditEvent(action, actor.user_id, version, detail))

    def view(self, package, actor):
        if not actor.can_view_private:
            self.metrics.rejected_actions += 1
            self._log("VIEW_DENIED", actor, package.version,
                      "Private draft access denied")
            raise GovernanceError("You do not have permission to view this draft.")
        self._log("VIEW", actor, package.version, "Draft viewed")
        return deepcopy(package)

    def edit(self, package, actor, new_body):
        if package.status != Status.DRAFT or not actor.can_approve:
            self.metrics.rejected_actions += 1
            self._log("EDIT_DENIED", actor, package.version,
                      "Only mailbox owner may edit a draft")
            raise GovernanceError("Only the mailbox owner can edit a draft.")
        package.body = new_body
        package.edits.append(f"Edited by {actor.user_id}")
        self._log("EDIT", actor, package.version, "Owner edited draft")
        return package

    def approve(self, package, actor):
        if package.status != Status.DRAFT or not actor.can_approve:
            self.metrics.rejected_actions += 1
            self._log("APPROVAL_DENIED", actor, package.version,
                      "Approval requires mailbox owner and draft state")
            raise GovernanceError("Only the mailbox owner can approve a draft.")
        package.status = Status.APPROVED
        package.approved_by = actor.user_id
        self.metrics.approvals += 1
        self._log("APPROVE", actor, package.version, "Draft approved")
        return package

    def publish(self, package, actor):
        if package.status != Status.APPROVED or not actor.can_approve:
            self.metrics.rejected_actions += 1
            self._log("PUBLISH_DENIED", actor, package.version,
                      "Publish requires owner-approved draft")
            raise GovernanceError("Only an owner-approved draft can be published.")
        self.current_version += 1
        package.version = self.current_version
        package.status = Status.PUBLISHED
        self.versions[self.current_version] = deepcopy(package)
        self.metrics.publications += 1
        self._log("PUBLISH", actor, package.version,
                  f"Published version {package.version}")
        return deepcopy(package)

    def rollback(self, version, actor):
        if not actor.can_approve:
            self.metrics.rejected_actions += 1
            self._log("ROLLBACK_DENIED", actor, self.current_version,
                      "Rollback requires mailbox owner")
            raise GovernanceError("Only the mailbox owner can roll back.")
        if version not in self.versions:
            raise ValueError(f"Version {version} does not exist.")
        restored = deepcopy(self.versions[version])
        self.current_version = version
        self.metrics.rollbacks += 1
        self._log("ROLLBACK", actor, version, f"Restored version {version}")
        return restored

    def evaluation_report(self):
        return {
            "approval_rate": (
                self.metrics.approvals / max(1, self.metrics.approvals + self.metrics.rejected_actions)
            ),
            "publications": self.metrics.publications,
            "rollbacks": self.metrics.rollbacks,
            "rejected_actions": self.metrics.rejected_actions,
            "audit_events": len(self.audit),
        }

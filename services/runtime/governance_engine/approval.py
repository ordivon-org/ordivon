from __future__ import annotations

from dataclasses import dataclass, field

from shared.time.clock import utc_now
from shared.utils.ids import new_id


VALID_APPROVAL_STATES = {"pending", "approved", "rejected", "expired"}


class ApprovalRequiredError(RuntimeError):
    def __init__(self, message: str, *, status_code: int = 409, approval_id: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.approval_id = approval_id


@dataclass
class ApprovalRecord:
    id: str = field(default_factory=lambda: new_id("approval"))
    action_key: str = ""
    entity_type: str = ""
    entity_id: str = ""
    status: str = "pending"
    requested_by: str = ""
    reason: str = ""
    note: str | None = None
    decided_by: str | None = None
    decided_note: str | None = None
    created_at: str = field(default_factory=lambda: utc_now().isoformat())
    decided_at: str | None = None

    def __post_init__(self) -> None:
        if not self.action_key:
            raise ValueError("ApprovalRecord requires action_key.")
        if not self.entity_type:
            raise ValueError("ApprovalRecord requires entity_type.")
        if not self.entity_id:
            raise ValueError("ApprovalRecord requires entity_id.")
        if self.status not in VALID_APPROVAL_STATES:
            raise ValueError(f"Unsupported approval state: {self.status}")
        if not self.requested_by:
            raise ValueError("ApprovalRecord requires requested_by.")
        if not self.reason:
            raise ValueError("ApprovalRecord requires reason.")


class HumanApprovalGate:
    def __init__(self, repository) -> None:
        self.repository = repository

    def request_approval(
        self,
        *,
        action_key: str,
        entity_type: str,
        entity_id: str,
        requested_by: str,
        reason: str,
        note: str | None = None,
    ):
        existing = self.repository.latest_for_action(action_key, entity_type=entity_type, entity_id=entity_id)
        if existing is not None and existing.status == "pending":
            return existing
        return self.repository.create(
            ApprovalRecord(
                action_key=action_key,
                entity_type=entity_type,
                entity_id=entity_id,
                requested_by=requested_by,
                reason=reason,
                note=note,
            )
        )

    def approve(self, approval_id: str, *, actor: str, note: str | None = None):
        row = self.repository.update_decision(
            approval_id,
            status="approved",
            decided_by=actor,
            decided_note=note,
        )
        if row is None:
            raise ApprovalRequiredError(f"Approval record not found: {approval_id}", status_code=404)
        return row

    def reject(self, approval_id: str, *, actor: str, note: str | None = None):
        row = self.repository.update_decision(
            approval_id,
            status="rejected",
            decided_by=actor,
            decided_note=note,
        )
        if row is None:
            raise ApprovalRequiredError(f"Approval record not found: {approval_id}", status_code=404)
        return row

    def ensure_approved(
        self,
        *,
        action_key: str,
        entity_type: str,
        entity_id: str,
        approval_id: str | None,
        require_approval: bool,
    ):
        if not require_approval:
            return None
        if not approval_id:
            raise ApprovalRequiredError(f"Approval required for {action_key}.")
        row = self.repository.get(approval_id)
        if row is None:
            raise ApprovalRequiredError(
                f"Approval record not found: {approval_id}",
                status_code=404,
                approval_id=approval_id,
            )
        if row.action_key != action_key or row.entity_type != entity_type or row.entity_id != entity_id:
            raise ApprovalRequiredError(
                f"Approval {approval_id} does not match {action_key} target.",
                approval_id=approval_id,
            )
        if row.status != "approved":
            raise ApprovalRequiredError(
                f"Approval {approval_id} is not approved (current state: {row.status}).",
                approval_id=approval_id,
            )
        return row

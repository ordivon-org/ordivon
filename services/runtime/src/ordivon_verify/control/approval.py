"""Human Approval Model — independent authority gate.

Enforces the Ordivon invariant: evidence ≠ approval, READY ≠ authorization.
The approval model is a SEPARATE concern from evidence, verification, and
readiness. A stage can be READY (all verification passed) but NOT APPROVED
(human has not signed off). This is by design.

Approval is required when:
  - authority_impact >= AI-2 (policy proposal or activation)
  - risk_class >= AP-R2 (integration or runtime effects)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from ordivon_verify.control.authority_state import (
    AuthorizationStatus, AuthorityLevel,
)
from ordivon_verify.control.stage_manifest import StageManifest, RiskClass, AuthorityImpact


@dataclass
class ApprovalGate:
    """An independent authorization check.

    An approval gate is NOT part of the verification pipeline. It is a
    SEPARATE human decision that happens AFTER evidence is collected and
    verification has passed.
    """
    stage_id: str
    required_level: AuthorityLevel
    status: AuthorizationStatus = AuthorizationStatus.NOT_REQUESTED
    approver: str = ""
    approved_at: str = ""
    rationale: str = ""
    expires_at: str = ""      # optional auto-expiry

    def request(self, approver: str = "") -> ApprovalGate:
        """Request human approval."""
        if self.status != AuthorizationStatus.NOT_REQUESTED:
            raise ValueError(f"Cannot request approval in status {self.status.value}")
        return ApprovalGate(
            stage_id=self.stage_id,
            required_level=self.required_level,
            status=AuthorizationStatus.REQUESTED,
            approver=approver,
        )

    def approve(self, approver: str, rationale: str,
                expires_hours: int = 0) -> ApprovalGate:
        """Human approves the stage."""
        if self.status != AuthorizationStatus.REQUESTED:
            raise ValueError(f"Cannot approve in status {self.status.value}")
        expires = ""
        if expires_hours > 0:
            exp = datetime.now(timezone.utc)
            exp = exp.replace(hour=exp.hour + expires_hours)
            expires = exp.isoformat()
        return ApprovalGate(
            stage_id=self.stage_id,
            required_level=self.required_level,
            status=AuthorizationStatus.APPROVED,
            approver=approver,
            approved_at=datetime.now(timezone.utc).isoformat(),
            rationale=rationale,
            expires_at=expires,
        )

    def reject(self, approver: str, rationale: str) -> ApprovalGate:
        """Human rejects the stage."""
        if self.status != AuthorizationStatus.REQUESTED:
            raise ValueError(f"Cannot reject in status {self.status.value}")
        return ApprovalGate(
            stage_id=self.stage_id,
            required_level=self.required_level,
            status=AuthorizationStatus.REJECTED,
            approver=approver,
            approved_at=datetime.now(timezone.utc).isoformat(),
            rationale=rationale,
        )

    @property
    def is_required(self) -> bool:
        """Is human approval required for this gate?"""
        return self.required_level in (
            AuthorityLevel.AI_2, AuthorityLevel.AI_3,
        )

    @property
    def is_satisfied(self) -> bool:
        """Is the approval gate satisfied?"""
        if not self.is_required:
            return True  # no approval needed
        return self.status == AuthorizationStatus.APPROVED

    @property
    def is_expired(self) -> bool:
        """Has the approval expired?"""
        if not self.expires_at:
            return False
        try:
            exp = datetime.fromisoformat(self.expires_at)
            return datetime.now(timezone.utc) > exp
        except (ValueError, TypeError):
            return False


def approval_required_for(manifest: StageManifest) -> bool:
    """Determine if human approval is required for this stage."""
    # AI-2+ always requires approval
    if manifest.authority_impact in (AuthorityImpact.AI_2, AuthorityImpact.AI_3):
        return True
    # AP-R2+ always requires approval
    if manifest.risk_class in (RiskClass.AP_R2, RiskClass.AP_R3):
        return True
    return False


def create_approval_gate(manifest: StageManifest) -> ApprovalGate:
    """Create an approval gate for a stage manifest."""
    # Map authority impact to required level
    level = AuthorityLevel(manifest.authority_impact.value)
    return ApprovalGate(
        stage_id=manifest.stage_id,
        required_level=level,
    )

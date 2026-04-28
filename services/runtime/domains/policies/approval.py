"""Policy Approval Gate + Rollback Contract — human review governance.

Pure domain logic. No ORM, no DB, no RiskEngine, no side effects.
Defines the approval process between shadow evaluation and any future
activation. Does NOT activate or enforce policies.

active_enforced approval is explicitly deferred — not allowed in this phase.
Only approved_for_shadow is permitted.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from domains.policies.models import (
    PolicyRecord,
    PolicyRollbackPlan,
    PolicyRisk,
    EvidenceFreshness,
)
from domains.policies.evidence_gate import (
    PolicyEvidenceGate,
    ReadinessLevel,
)
from domains.policies.shadow import (
    ShadowVerdict,
)


class ApprovalOutcome(str, Enum):
    """The result of a policy approval review."""

    APPROVED_FOR_SHADOW = "approved_for_shadow"
    REJECTED = "rejected"
    NEEDS_MORE_EVIDENCE = "needs_more_evidence"
    NEEDS_MORE_SHADOW = "needs_more_shadow"
    DEFERRED = "deferred"  # e.g., active_enforced not yet allowed


class ReviewerRole(str, Enum):
    """Roles required for policy approval."""

    TECHNICAL_REVIEWER = "technical_reviewer"
    DOMAIN_OWNER = "domain_owner"
    GOVERNANCE_REVIEWER = "governance_reviewer"


@dataclass(frozen=True)
class Reviewer:
    """A named reviewer with a role."""

    reviewer_id: str
    role: ReviewerRole

    def __post_init__(self):
        if not self.reviewer_id.strip():
            raise ValueError("Reviewer requires reviewer_id.")


# ══════════════════════════════════════════════════════════════════════
# Rollback Contract
# ══════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class PolicyRollbackContract:
    """A validated rollback contract that must accompany every approval.

    Extends PolicyRollbackPlan with post-rollback review requirements.
    Every field is required — no optional fields.
    """

    trigger: str
    authorized_by: str
    method: str
    blast_radius: str
    target_recovery_time: str
    post_rollback_review_required: bool = True
    post_rollback_reviewer: str = ""

    def __post_init__(self):
        required = {
            "trigger": self.trigger,
            "authorized_by": self.authorized_by,
            "method": self.method,
            "blast_radius": self.blast_radius,
            "target_recovery_time": self.target_recovery_time,
        }
        for field_name, value in required.items():
            if not (value or "").strip():
                raise ValueError(f"PolicyRollbackContract requires {field_name}.")
        if self.post_rollback_review_required and not self.post_rollback_reviewer.strip():
            raise ValueError(
                "PolicyRollbackContract requires post_rollback_reviewer when post_rollback_review_required is True."
            )

    @classmethod
    def from_rollback_plan(
        cls, plan: PolicyRollbackPlan, *, post_rollback_reviewer: str = ""
    ) -> PolicyRollbackContract:
        """Create a validated rollback contract from a PolicyRollbackPlan."""
        return cls(
            trigger=plan.trigger,
            authorized_by=plan.authorized_by,
            method=plan.method,
            blast_radius=plan.blast_radius,
            target_recovery_time=plan.target_recovery_time,
            post_rollback_reviewer=post_rollback_reviewer,
        )


# ══════════════════════════════════════════════════════════════════════
# Approval Request & Decision
# ══════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class PolicyApprovalRequest:
    """A request for human approval of a policy to advance toward shadow.

    Bundles the policy, its evidence gate result, shadow evaluation
    summary, reviewers, and rollback contract for a single approval
    decision.
    """

    policy: PolicyRecord
    evidence_readiness: ReadinessLevel
    shadow_summary: str  # human-readable summary of shadow results
    shadow_verdicts: tuple[ShadowVerdict, ...]  # all shadow verdicts
    reviewers: tuple[Reviewer, ...]
    rollback_contract: PolicyRollbackContract | None = None
    requested_outcome: str = "approved_for_shadow"  # only shadow is allowed now


@dataclass(frozen=True)
class PolicyApprovalDecision:
    """The result of a policy approval review.

    Immutable. Records the decision, rationale, and reviewer identities.
    """

    policy_id: str
    outcome: ApprovalOutcome
    rationale: str
    reviewers: tuple[Reviewer, ...] = ()
    conditions: tuple[str, ...] = ()  # conditions that must be met before re-review


# ══════════════════════════════════════════════════════════════════════
# Approval Gate
# ══════════════════════════════════════════════════════════════════════


class PolicyApprovalGate:
    """Validates whether a PolicyApprovalRequest should be approved.

    Enforces the governance rules between shadow evaluation and activation.
    Only approved_for_shadow is permitted in this phase.
    active_enforced is explicitly deferred.

    Pure domain logic. No side effects. Never mutates PolicyRecord.
    """

    def __init__(self):
        self._evidence_gate = PolicyEvidenceGate()

    def review(self, request: PolicyApprovalRequest) -> PolicyApprovalDecision:
        """Review a PolicyApprovalRequest and produce a decision.

        Returns a PolicyApprovalDecision. Never mutates the policy.
        """
        policy = request.policy

        # ── Gate 0: active_enforced is deferred ──────────────────
        if request.requested_outcome != "approved_for_shadow":
            return PolicyApprovalDecision(
                policy_id=policy.policy_id,
                outcome=ApprovalOutcome.DEFERRED,
                rationale=(
                    f"Cannot approve '{request.requested_outcome}'. "
                    "Only 'approved_for_shadow' is permitted in Phase 5. "
                    "active_enforced approval requires a separate governance phase."
                ),
                reviewers=request.reviewers,
            )

        # ── Gate 1: Evidence readiness ───────────────────────────
        if request.evidence_readiness == ReadinessLevel.NOT_READY:
            return PolicyApprovalDecision(
                policy_id=policy.policy_id,
                outcome=ApprovalOutcome.NEEDS_MORE_EVIDENCE,
                rationale="Evidence is not ready for review. See evidence gate results.",
                reviewers=request.reviewers,
            )

        # ── Gate 2: No stale-only evidence ───────────────────────
        if policy.evidence_refs:
            all_stale = all(r.freshness == EvidenceFreshness.STALE for r in policy.evidence_refs)
            if all_stale:
                return PolicyApprovalDecision(
                    policy_id=policy.policy_id,
                    outcome=ApprovalOutcome.NEEDS_MORE_EVIDENCE,
                    rationale="All evidence is stale. Regenerate or provide human exception.",
                    reviewers=request.reviewers,
                )

        # ── Gate 3: Owner is required ────────────────────────────
        if policy.owner is None:
            return PolicyApprovalDecision(
                policy_id=policy.policy_id,
                outcome=ApprovalOutcome.REJECTED,
                rationale="Policy has no owner. An owner must be assigned before approval.",
                reviewers=request.reviewers,
            )

        # ── Gate 4: Rollback contract is required ────────────────
        if request.rollback_contract is None:
            return PolicyApprovalDecision(
                policy_id=policy.policy_id,
                outcome=ApprovalOutcome.REJECTED,
                rationale="No rollback contract provided. A PolicyRollbackContract is required before approval.",
                reviewers=request.reviewers,
            )

        # ── Gate 5: Shadow results must not be WOULD_REJECT ──────
        if ShadowVerdict.WOULD_REJECT in request.shadow_verdicts:
            return PolicyApprovalDecision(
                policy_id=policy.policy_id,
                outcome=ApprovalOutcome.REJECTED,
                rationale=(
                    "Shadow evaluation produced WOULD_REJECT verdict(s). "
                    "Policy must not advance when it would reject valid actions."
                ),
                reviewers=request.reviewers,
            )

        # ── Gate 6: Shadow WOULD_HOLD → needs more shadow ────────
        if ShadowVerdict.WOULD_HOLD in request.shadow_verdicts:
            return PolicyApprovalDecision(
                policy_id=policy.policy_id,
                outcome=ApprovalOutcome.NEEDS_MORE_SHADOW,
                rationale=(
                    "Shadow evaluation produced WOULD_HOLD verdict(s). "
                    "Address hold conditions and re-evaluate before approval."
                ),
                reviewers=request.reviewers,
                conditions=("Resolve hold conditions in shadow evaluation.",),
            )

        # ── Gate 7: Risk classification check ────────────────────
        if policy.risk in (PolicyRisk.MEDIUM, PolicyRisk.HIGH):
            gov_reviewers = [r for r in request.reviewers if r.role == ReviewerRole.GOVERNANCE_REVIEWER]
            if not gov_reviewers:
                return PolicyApprovalDecision(
                    policy_id=policy.policy_id,
                    outcome=ApprovalOutcome.REJECTED,
                    rationale=(
                        f"Policy risk is '{policy.risk.value}'. "
                        "A governance reviewer is required for medium/high risk policies."
                    ),
                    reviewers=request.reviewers,
                )

        # ── Gate 8: Reviewer minimum ─────────────────────────────
        if not request.reviewers:
            return PolicyApprovalDecision(
                policy_id=policy.policy_id,
                outcome=ApprovalOutcome.REJECTED,
                rationale="At least one reviewer is required for approval.",
            )

        # ── All gates passed → approved_for_shadow ───────────────
        return PolicyApprovalDecision(
            policy_id=policy.policy_id,
            outcome=ApprovalOutcome.APPROVED_FOR_SHADOW,
            rationale=(
                "All approval gates passed. Policy is approved for shadow evaluation. "
                "active_enforced activation requires a separate governance phase."
            ),
            reviewers=request.reviewers,
        )

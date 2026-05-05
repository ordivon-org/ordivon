"""Authority State Model — Ordivon Control Plane.

Enforces the core philosophical invariant:
    evidence ≠ approval
    READY ≠ authorization
    CandidateRule ≠ Policy

These four state machines are INDEPENDENT. A receipt can be READY
without being APPROVED. A CandidateRule can have sufficient EVIDENCE
without becoming ADOPTED policy. Confusing these states is the #1
governance failure mode in AI-assisted workflows.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


# ═══════════════════════════════════════════════════════════════════
# State Enums
# ═══════════════════════════════════════════════════════════════════


class EvidenceStatus(str, Enum):
    """How much evidence supports a claim. Independent of authorization."""

    MISSING = "missing"  # no evidence at all
    PARTIAL = "partial"  # some evidence, but gaps
    SUFFICIENT = "sufficient"  # evidence meets requirements
    CONTRADICTED = "contradicted"  # evidence conflicts with itself


class ReadinessStatus(str, Enum):
    """Is the stage ready for review? Independent of authorization."""

    NOT_READY = "not_ready"  # work incomplete
    READY_FOR_REVIEW = "ready_for_review"  # work complete, evidence present
    CLOSED_CURRENT_TRUTH = "closed_current_truth"  # truth state updated


class AuthorizationStatus(str, Enum):
    """Has a human authorized action? Independent of evidence."""

    NOT_REQUESTED = "not_requested"
    REQUESTED = "requested"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class PolicyStatus(str, Enum):
    """Lifecycle of a governance rule or policy."""

    CANDIDATE = "candidate"  # proposed, not binding
    EXPERIMENTAL = "experimental"  # active in shadow/test mode
    ADOPTED = "adopted"  # active, blocking
    DEPRECATED = "deprecated"  # scheduled for removal
    REVOKED = "revoked"  # emergency removal


# ═══════════════════════════════════════════════════════════════════
# Authority Level
# ═══════════════════════════════════════════════════════════════════


class AuthorityLevel(str, Enum):
    """What level of authority does this action require?"""

    AI_0 = "AI-0"  # current_truth only — agent can close
    AI_1 = "AI-1"  # governance docs/schemas — agent can propose
    AI_2 = "AI-2"  # policy proposal/evidence — human must review
    AI_3 = "AI-3"  # policy activation/publish/release — human must approve


# ═══════════════════════════════════════════════════════════════════
# Document Layer
# ═══════════════════════════════════════════════════════════════════


class DocumentLayer(str, Enum):
    """Memory hierarchy layer for governance documents."""

    L0_ROOT = "L0"  # entry point — AGENTS.md, docs/ai/README.md
    L1_TRUTH = "L1"  # current truth — phase boundaries, systems reference
    L2_EVIDENCE = "L2"  # runtime evidence — receipts, command outputs
    L3_CANON = "L3"  # governance canon — risk ladder, authority model
    L4_PRODUCT = "L4"  # product notes — roadmap, strategy, stage notes
    L5_ARCHIVE = "L5"  # historical — superseded docs, old receipts


class DocumentAuthority(str, Enum):
    """What kind of authority does a document carry?"""

    SOURCE_OF_TRUTH = "source_of_truth"  # this document MAKES claims
    CURRENT_STATUS = "current_status"  # this document REPORTS state
    SUPPORTING_EVIDENCE = "supporting_evidence"  # this document SUPPORTS claims
    HISTORICAL_RECORD = "historical_record"  # this document RECORDS history
    PROPOSAL = "proposal"  # this document PROPOSES changes
    ARCHIVE = "archive"  # this document is RETIRED


# ═══════════════════════════════════════════════════════════════════
# Transition validation
# ═══════════════════════════════════════════════════════════════════

# Evidence transitions: progressive, but can be contradicted at any point
VALID_EVIDENCE_TRANSITIONS = {
    EvidenceStatus.MISSING: {EvidenceStatus.MISSING, EvidenceStatus.PARTIAL},
    EvidenceStatus.PARTIAL: {EvidenceStatus.PARTIAL, EvidenceStatus.SUFFICIENT, EvidenceStatus.CONTRADICTED},
    EvidenceStatus.SUFFICIENT: {EvidenceStatus.SUFFICIENT, EvidenceStatus.CONTRADICTED},
    EvidenceStatus.CONTRADICTED: {EvidenceStatus.CONTRADICTED, EvidenceStatus.PARTIAL},
}

# Authorization: NOT_REQUESTED → REQUESTED → APPROVED/REJECTED → EXPIRED
VALID_AUTH_TRANSITIONS = {
    AuthorizationStatus.NOT_REQUESTED: {AuthorizationStatus.NOT_REQUESTED, AuthorizationStatus.REQUESTED},
    AuthorizationStatus.REQUESTED: {
        AuthorizationStatus.REQUESTED,
        AuthorizationStatus.APPROVED,
        AuthorizationStatus.REJECTED,
        AuthorizationStatus.EXPIRED,
    },
    AuthorizationStatus.APPROVED: {AuthorizationStatus.APPROVED, AuthorizationStatus.EXPIRED},
    AuthorizationStatus.REJECTED: {AuthorizationStatus.REJECTED, AuthorizationStatus.REQUESTED},
    AuthorizationStatus.EXPIRED: {AuthorizationStatus.EXPIRED, AuthorizationStatus.REQUESTED},
}

# Policy: progressive, with emergency revoke from ADOPTED
VALID_POLICY_TRANSITIONS = {
    PolicyStatus.CANDIDATE: {PolicyStatus.CANDIDATE, PolicyStatus.EXPERIMENTAL},
    PolicyStatus.EXPERIMENTAL: {PolicyStatus.EXPERIMENTAL, PolicyStatus.ADOPTED, PolicyStatus.DEPRECATED},
    PolicyStatus.ADOPTED: {PolicyStatus.ADOPTED, PolicyStatus.DEPRECATED, PolicyStatus.REVOKED},
    PolicyStatus.DEPRECATED: {PolicyStatus.DEPRECATED, PolicyStatus.REVOKED},
    PolicyStatus.REVOKED: frozenset(),  # terminal — cannot be reinstated, create new
}


class InvalidTransitionError(Exception):
    """Raised when a state transition is not allowed."""

    pass


# ═══════════════════════════════════════════════════════════════════
# Authority State container
# ═══════════════════════════════════════════════════════════════════


@dataclass
class AuthorityState:
    """The four independent state dimensions for a governance stage.

    These are intentionally SEPARATE. A stage can be:
    - Evidence=SUFFICIENT but Authorization=NOT_REQUESTED
    - Readiness=READY but Policy=CANDIDATE
    - Evidence=SUFFICIENT, Readiness=READY, Authorization=NOT_REQUESTED → normal
    """

    evidence: EvidenceStatus = EvidenceStatus.MISSING
    readiness: ReadinessStatus = ReadinessStatus.NOT_READY
    authorization: AuthorizationStatus = AuthorizationStatus.NOT_REQUESTED
    policy: PolicyStatus = PolicyStatus.CANDIDATE

    def transition_evidence(self, target: EvidenceStatus, reason: str = "") -> AuthorityState:
        if target not in VALID_EVIDENCE_TRANSITIONS.get(self.evidence, set()):
            raise InvalidTransitionError(f"Evidence: {self.evidence.value} → {target.value} is not allowed")
        return AuthorityState(
            evidence=target, readiness=self.readiness, authorization=self.authorization, policy=self.policy
        )

    def transition_authorization(
        self, target: AuthorizationStatus, approver: str = "", rationale: str = ""
    ) -> AuthorityState:
        if target not in VALID_AUTH_TRANSITIONS.get(self.authorization, set()):
            raise InvalidTransitionError(f"Authorization: {self.authorization.value} → {target.value} is not allowed")
        return AuthorityState(
            evidence=self.evidence, readiness=self.readiness, authorization=target, policy=self.policy
        )

    def transition_policy(self, target: PolicyStatus) -> AuthorityState:
        if target not in VALID_POLICY_TRANSITIONS.get(self.policy, set()):
            raise InvalidTransitionError(f"Policy: {self.policy.value} → {target.value} is not allowed")
        return AuthorityState(
            evidence=self.evidence, readiness=self.readiness, authorization=self.authorization, policy=target
        )

    # ── Safety predicates ──────────────────────────────────────────

    @property
    def is_safe_to_proceed(self) -> bool:
        """Can the agent proceed without human intervention?

        True only when: evidence is sufficient, readiness confirms,
        authorization is not required (AI-0/AI-1), and no policy change.
        """
        return (
            self.evidence in (EvidenceStatus.SUFFICIENT,)
            and self.readiness != ReadinessStatus.NOT_READY
            and self.authorization != AuthorizationStatus.REJECTED
            and self.policy != PolicyStatus.REVOKED
        )

    @property
    def requires_human_approval(self) -> bool:
        """Does this state require human authorization to proceed?"""
        return self.authorization in (
            AuthorizationStatus.REQUESTED,
            AuthorizationStatus.APPROVED,
        ) or self.policy in (PolicyStatus.ADOPTED,)

    @property
    def has_authority_confusion(self) -> bool:
        """Is there a dangerous conflation of independent states?

        The #1 governance failure: treating READY as APPROVED, or
        treating SUFFICIENT evidence as ADOPTED policy.
        """
        # "APPROVED" without explicit authorization request = confusion
        if self.authorization == AuthorizationStatus.APPROVED:
            return True  # approval must be explicit, not inferred from READY
        # ADOPTED policy without evidence = confusion
        if self.policy == PolicyStatus.ADOPTED and self.evidence != EvidenceStatus.SUFFICIENT:
            return True
        return False

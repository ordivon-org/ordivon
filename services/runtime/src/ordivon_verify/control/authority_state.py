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


# ── OPA-backed transition validation (Phase 3) ─────────────────────────────
# Delegates to OPA Rego policies for validation. Falls back to hardcoded
# VALID_*_TRANSITIONS dicts when OPA is unavailable.


def check_transition_opa(
    from_evidence: str,
    from_authorization: str,
    from_policy: str,
    from_readiness: str = "ready_for_review",
    to_evidence: str = "",
    to_authorization: str = "",
    to_policy: str = "",
) -> dict:
    """Validate a governance authority transition using OPA Rego.

    Args:
        from_evidence, from_authorization, from_policy: Current states
        to_evidence, to_authorization, to_policy: Target states (empty = no transition)

    Returns:
        dict with keys:
            all_valid: bool
            evidence_valid: bool
            authorization_valid: bool
            policy_valid: bool
            safe_to_proceed: bool
            requires_human_approval: bool
            has_authority_confusion: bool
            blocked_reasons: list[str]
            backend: "opa" | "python_fallback"
    """
    from ordivon_governance_core.opa_engine import opa_available, _opa_eval

    if opa_available():
        try:
            input_data = {
                "state": {
                    "evidence": from_evidence,
                    "readiness": from_readiness,
                    "authorization": from_authorization,
                    "policy": from_policy,
                },
                "target": {
                    "evidence": to_evidence,
                    "authorization": to_authorization,
                    "policy": to_policy,
                },
            }
            result = _opa_eval(
                "data.ordivon.authority.validate_transition",
                input_data,
                # POLICY_DIR already loads all .rego files — no need for extra data_files
            )
            if "error" not in result:
                for r in result.get("result", []):
                    for expr in r.get("expressions", []):
                        val = expr.get("value")
                        if isinstance(val, dict) and "all_valid" in val:
                            val["backend"] = "opa"
                            return val
        except Exception:
            pass

    # Python fallback
    return _check_transition_python(
        from_evidence,
        from_authorization,
        from_policy,
        from_readiness,
        to_evidence,
        to_authorization,
        to_policy,
    )


def _check_transition_python(
    from_evidence: str,
    from_authorization: str,
    from_policy: str,
    from_readiness: str = "ready_for_review",
    to_evidence: str = "",
    to_authorization: str = "",
    to_policy: str = "",
) -> dict:
    """Fallback transition validation using hardcoded Python dicts."""
    evidence_valid = True
    if to_evidence:
        allowed = VALID_EVIDENCE_TRANSITIONS.get(EvidenceStatus(from_evidence), set())
        evidence_valid = EvidenceStatus(to_evidence) in allowed

    authorization_valid = True
    if to_authorization:
        allowed = VALID_AUTH_TRANSITIONS.get(AuthorizationStatus(from_authorization), set())
        authorization_valid = AuthorizationStatus(to_authorization) in allowed

    policy_valid = True
    if to_policy:
        allowed = VALID_POLICY_TRANSITIONS.get(PolicyStatus(from_policy), set())
        policy_valid = PolicyStatus(to_policy) in allowed

    state = AuthorityState(
        evidence=EvidenceStatus(from_evidence),
        readiness=ReadinessStatus(from_readiness),
        authorization=AuthorizationStatus(from_authorization),
        policy=PolicyStatus(from_policy),
    )

    blocked_reasons = []
    if not evidence_valid:
        blocked_reasons.append("evidence_transition_blocked")
    if not authorization_valid:
        blocked_reasons.append("authorization_transition_blocked")
    if not policy_valid:
        blocked_reasons.append("policy_transition_blocked")

    return {
        "all_valid": evidence_valid and authorization_valid and policy_valid,
        "evidence_valid": evidence_valid,
        "authorization_valid": authorization_valid,
        "policy_valid": policy_valid,
        "safe_to_proceed": state.is_safe_to_proceed,
        "requires_human_approval": state.requires_human_approval,
        "has_authority_confusion": state.has_authority_confusion,
        "blocked_reasons": blocked_reasons,
        "backend": "python_fallback",
    }

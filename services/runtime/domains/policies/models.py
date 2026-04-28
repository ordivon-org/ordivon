"""Policy Platform — pure domain models (Phase 5.2 prototype).

No ORM, no DB schema, no RiskEngine integration, no side effects.
These are value objects and enums for the Policy lifecycle as designed
in docs/architecture/policy-platform-design.md.

Does NOT: create active/enforced policies, modify Pack policies,
interact with RiskEngine, import governance or execution modules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


# ── Enums ────────────────────────────────────────────────────────────


class PolicyScope(str, Enum):
    """The domain scope a Policy applies to."""

    CORE = "core"
    PACK = "pack"
    ADAPTER = "adapter"
    VERIFICATION = "verification"
    SECURITY = "security"


class PolicyState(str, Enum):
    """The lifecycle state of a Policy.

    Terminal states: deprecated, rolled_back, rejected.
    """

    DRAFT = "draft"
    PROPOSED = "proposed"
    APPROVED = "approved"
    ACTIVE_SHADOW = "active_shadow"  # enforced in shadow mode (advisory, not blocking)
    ACTIVE_ENFORCED = "active_enforced"  # enforced as blocking
    DEPRECATED = "deprecated"  # intentionally retired (terminal)
    ROLLED_BACK = "rolled_back"  # emergency-removed (terminal)
    REJECTED = "rejected"  # permanently rejected (terminal)


class PolicyRisk(str, Enum):
    """The risk level of an active Policy."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class EvidenceFreshness(str, Enum):
    """Freshness classification of an evidence reference."""

    CURRENT = "current"
    STALE = "stale"
    REGENERATED = "regenerated"
    HUMAN_EXCEPTION = "human_exception"


class OwnerType(str, Enum):
    """The type of Policy owner."""

    INDIVIDUAL = "individual"
    ROLE = "role"
    TEAM = "team"


# ── Value Objects ────────────────────────────────────────────────────


@dataclass(frozen=True)
class PolicyEvidenceRef:
    """A reference to evidence that supports this Policy.

    Maps to doctrine §3 (Evidence Before Belief) and §5 (Evidence Freshness Rules).
    """

    ref_type: str  # e.g., "candidate_rule", "lesson", "ci_artifact", "eval_result"
    ref_id: str  # unique identifier for the evidence source
    freshness: EvidenceFreshness = EvidenceFreshness.CURRENT

    def __post_init__(self):
        if not self.ref_type.strip():
            raise ValueError("PolicyEvidenceRef requires ref_type.")
        if not self.ref_id.strip():
            raise ValueError("PolicyEvidenceRef requires ref_id.")


@dataclass(frozen=True)
class PolicyRollbackPlan:
    """A rollback plan required before Policy activation.

    Maps to Phase 5.1 design §5.5: every Policy must have a rollback plan
    documented BEFORE activation.
    """

    trigger: str  # what triggers rollback (e.g., "false positive rate > 5%")
    authorized_by: str  # who can authorize rollback
    method: str  # how rollback is executed (e.g., "state transition", "config flag")
    blast_radius: str  # what is affected by rollback (e.g., "CI gate repo-governance-pr")
    target_recovery_time: str  # how long rollback takes (e.g., "seconds", "deploy cycle")

    def __post_init__(self):
        if not all(
            [
                self.trigger.strip(),
                self.authorized_by.strip(),
                self.method.strip(),
                self.blast_radius.strip(),
                self.target_recovery_time.strip(),
            ]
        ):
            raise ValueError("PolicyRollbackPlan requires all fields to be non-empty.")


@dataclass(frozen=True)
class PolicyOwner:
    """The named owner of a Policy.

    Maps to Phase 5.1 design §5.3: every active Policy must have a named owner.
    """

    owner_id: str
    owner_type: OwnerType = OwnerType.INDIVIDUAL

    def __post_init__(self):
        if not self.owner_id.strip():
            raise ValueError("PolicyOwner requires owner_id.")


# ── Policy Record ────────────────────────────────────────────────────


@dataclass(frozen=True)
class PolicyRecord:
    """A Policy entity in the governance platform.

    Immutable value object. State transitions produce new PolicyRecord
    instances (immutable Policy records pattern per Phase 5.1 §9.2 option B).
    """

    policy_id: str
    title: str
    scope: PolicyScope
    state: PolicyState
    risk: PolicyRisk
    evidence_refs: tuple[PolicyEvidenceRef, ...] = ()
    owner: PolicyOwner | None = None
    rollback_plan: PolicyRollbackPlan | None = None
    version: int = 1
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    predecessor_policy_id: str | None = None  # lineage tracking
    rollback_reason: str | None = None  # required for rolled_back state
    deprecation_reason: str | None = None  # required for deprecated state

    def __post_init__(self):
        if not self.policy_id.strip():
            raise ValueError("PolicyRecord requires policy_id.")
        if not self.title.strip():
            raise ValueError("PolicyRecord requires title.")

    def with_state(self, new_state: PolicyState, **overrides) -> PolicyRecord:
        """Return a new PolicyRecord with updated state and optional field overrides.

        Does NOT validate state transitions — use PolicyStateMachine for that.
        """
        kwargs = {
            "policy_id": self.policy_id,
            "title": self.title,
            "scope": self.scope,
            "state": new_state,
            "risk": overrides.get("risk", self.risk),
            "evidence_refs": overrides.get("evidence_refs", self.evidence_refs),
            "owner": overrides.get("owner", self.owner),
            "rollback_plan": overrides.get("rollback_plan", self.rollback_plan),
            "version": overrides.get("version", self.version + 1),
            "created_at": overrides.get("created_at", datetime.now(timezone.utc)),
            "predecessor_policy_id": overrides.get("predecessor_policy_id", self.policy_id),
            "rollback_reason": overrides.get("rollback_reason", None),
            "deprecation_reason": overrides.get("deprecation_reason", None),
        }
        return PolicyRecord(**kwargs)

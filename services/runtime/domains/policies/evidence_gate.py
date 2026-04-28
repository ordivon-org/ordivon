"""Policy Evidence Gate — validates whether a PolicyRecord has sufficient
evidence to proceed through review stages.

Pure domain logic. No ORM, no DB, no RiskEngine, no side effects.
Does NOT activate or enforce policies.

Readiness levels (ascending):
  NOT_READY            — insufficient evidence, cannot proceed
  READY_FOR_REVIEW     — enough evidence for human review, not for activation
  READY_FOR_SHADOW     — ready for shadow evaluation (advisory only)
  READY_FOR_ACTIVATION — ready for active_enforced (blocking)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from domains.policies.models import (
    PolicyRecord,
    EvidenceFreshness,
    PolicyRisk,
)


class ReadinessLevel(str, Enum):
    """How ready a Policy is for the next governance stage."""

    NOT_READY = "not_ready"
    READY_FOR_REVIEW = "ready_for_review"  # human review of draft
    READY_FOR_SHADOW = "ready_for_shadow"  # shadow/advisory evaluation
    READY_FOR_ACTIVATION = "ready_for_activation"  # active_enforced


# Ref types that count as legitimate evidence sources
_ALLOWED_EVIDENCE_REF_TYPES: frozenset[str] = frozenset(
    {
        "candidate_rule",
        "lesson",
        "review",
        "recommendation",
        "ci_artifact",
        "eval_result",
        "source_ref",
        "audit_event",
    }
)

# Ref types that are INSIDE the Ordivon learning loop (strong evidence)
_LEARNING_LOOP_REF_TYPES: frozenset[str] = frozenset(
    {
        "candidate_rule",
        "lesson",
        "review",
        "recommendation",
    }
)

# Evidence that is explicitly NOT sufficient alone for activation
_WEAK_SOLO_REF_TYPES: frozenset[str] = frozenset(
    {
        "ci_artifact",  # CI artifacts are raw evidence, not governance analysis
        "source_ref",  # generic source ref, lacks governance context
        "audit_event",  # audit events are records, not policy rationale
    }
)


@dataclass(frozen=True)
class EvidenceGateResult:
    """The result of an evidence readiness check."""

    level: ReadinessLevel
    reasons: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    @property
    def is_ready(self) -> bool:
        return self.level != ReadinessLevel.NOT_READY


class PolicyEvidenceGate:
    """Validates whether a PolicyRecord has sufficient evidence to advance.

    Pure domain logic. Does NOT modify policy state or activate anything.
    """

    def assess(self, policy: PolicyRecord) -> EvidenceGateResult:
        """Assess whether a PolicyRecord is ready for its next governance stage.

        Returns an EvidenceGateResult with a ReadinessLevel and reasons/warnings.
        """
        reasons: list[str] = []
        warnings: list[str] = []

        # ── Gate 1: Evidence exists ──────────────────────────────
        if not policy.evidence_refs:
            return EvidenceGateResult(
                level=ReadinessLevel.NOT_READY,
                reasons=("No evidence_refs. At least one PolicyEvidenceRef is required.",),
            )

        # ── Gate 2: All ref_types are valid ──────────────────────
        for ref in policy.evidence_refs:
            if ref.ref_type not in _ALLOWED_EVIDENCE_REF_TYPES:
                reasons.append(
                    f"Unknown evidence ref_type '{ref.ref_type}' in ref '{ref.ref_id}'. "
                    f"Allowed types: {sorted(_ALLOWED_EVIDENCE_REF_TYPES)}."
                )

        # ── Gate 3: Evidence freshness ───────────────────────────
        stale_count = sum(1 for r in policy.evidence_refs if r.freshness == EvidenceFreshness.STALE)
        if stale_count > 0:
            reasons.append(
                f"{stale_count} evidence ref(s) have STALE freshness. "
                "Stale evidence must be regenerated or marked as human_exception before proceeding."
            )

        current_or_regen = sum(
            1 for r in policy.evidence_refs if r.freshness in (EvidenceFreshness.CURRENT, EvidenceFreshness.REGENERATED)
        )
        if current_or_regen == 0:
            reasons.append(
                "No evidence with CURRENT or REGENERATED freshness. At least one fresh evidence ref is required."
            )

        # ── Gate 4: Scope must exist ─────────────────────────────
        if not policy.scope:
            reasons.append("Policy scope is required.")

        # ── Gate 5: Risk classification must exist ───────────────
        if not policy.risk:
            reasons.append("Policy risk classification is required.")

        # ── Gate 6: Single-event evidence is weak ───────────────
        unique_ref_types = {r.ref_type for r in policy.evidence_refs}
        has_weak_solo = len(unique_ref_types) == 1 and next(iter(unique_ref_types)) in _WEAK_SOLO_REF_TYPES
        if has_weak_solo:
            weak_type = next(iter(unique_ref_types))
            warnings.append(
                f"Evidence consists only of '{weak_type}' ref(s). "
                "This is insufficient for activation. Requires evidence from the learning loop "
                f"(candidate_rule, lesson, review, recommendation) or multiple independent sources."
            )

        # ── Gate 7: Learning loop lineage check ──────────────────
        learning_loop_refs = [r for r in policy.evidence_refs if r.ref_type in _LEARNING_LOOP_REF_TYPES]
        if not learning_loop_refs:
            warnings.append(
                "No evidence from the Ordivon learning loop "
                "(candidate_rule, lesson, review, recommendation). "
                "Policy based solely on external evidence requires explicit human exception."
            )

        # ── Determine readiness level ────────────────────────────
        if reasons:
            return EvidenceGateResult(
                level=ReadinessLevel.NOT_READY,
                reasons=tuple(reasons),
                warnings=tuple(warnings),
            )

        # Check activation-specific requirements
        owner_ready = policy.owner is not None
        rollback_ready = policy.rollback_plan is not None

        if owner_ready and rollback_ready and not has_weak_solo and learning_loop_refs:
            return EvidenceGateResult(
                level=ReadinessLevel.READY_FOR_ACTIVATION,
                warnings=tuple(warnings),
            )
        elif owner_ready and rollback_ready:
            return EvidenceGateResult(
                level=ReadinessLevel.READY_FOR_SHADOW,
                warnings=tuple(warnings),
            )
        else:
            missing = []
            if not owner_ready:
                missing.append("owner")
            if not rollback_ready:
                missing.append("rollback_plan")
            return EvidenceGateResult(
                level=ReadinessLevel.READY_FOR_REVIEW,
                reasons=(f"Ready for human review, but missing: {', '.join(missing)}.",),
                warnings=tuple(warnings),
            )


# ══════════════════════════════════════════════════════════════════════
# Review Checklist
# ══════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class ChecklistItem:
    """A single item in the Policy review checklist."""

    question: str
    status: str  # "pass", "fail", "warn", "pending"
    detail: str = ""


@dataclass
class PolicyReviewChecklist:
    """A structured review checklist for a PolicyRecord.

    Answers the key governance questions that must be addressed before
    a Policy can advance beyond draft. This is a human-auditable checklist,
    not an automated gate — the evidence gate handles automated validation.
    """

    policy_id: str
    items: list[ChecklistItem] = field(default_factory=list)
    overall_ready: bool = False

    def build(self, policy: PolicyRecord, gate_result: EvidenceGateResult) -> PolicyReviewChecklist:
        """Build a review checklist from a PolicyRecord and evidence gate result."""
        self.policy_id = policy.policy_id
        self.items = []

        # 1. Problem definition
        self.items.append(
            ChecklistItem(
                question="What problem does this policy address?",
                status="pass" if policy.title.strip() else "fail",
                detail=policy.title,
            )
        )

        # 2. Evidence existence
        self.items.append(
            ChecklistItem(
                question="What evidence supports this policy?",
                status="pass" if policy.evidence_refs else "fail",
                detail=f"{len(policy.evidence_refs)} evidence ref(s)",
            )
        )

        # 3. Evidence freshness
        stale = sum(1 for r in policy.evidence_refs if r.freshness == EvidenceFreshness.STALE)
        self.items.append(
            ChecklistItem(
                question="Is evidence fresh?",
                status="fail" if stale > 0 else "pass",
                detail=f"{stale} stale ref(s)" if stale else "All evidence is current or regenerated",
            )
        )

        # 4. Multi-incident basis
        unique_types = {r.ref_type for r in policy.evidence_refs}
        self.items.append(
            ChecklistItem(
                question="Is this based on more than one incident?",
                status="warn" if len(unique_types) <= 1 else "pass",
                detail=f"{len(unique_types)} evidence type(s): {sorted(unique_types)}",
            )
        )

        # 5. Actor / Adapter / Pack / Scope
        self.items.append(
            ChecklistItem(
                question="What actor / adapter / pack / scope does this affect?",
                status="pass",
                detail=f"scope={policy.scope.value}",
            )
        )

        # 6. False positive risk
        risk_map = {"low": "Low risk of false positives", "medium": "Moderate risk", "high": "High risk"}
        self.items.append(
            ChecklistItem(
                question="What is the false positive risk?",
                status="warn" if policy.risk in (PolicyRisk.MEDIUM, PolicyRisk.HIGH) else "pass",
                detail=risk_map.get(policy.risk.value, "Unknown"),
            )
        )

        # 7. Rollback plan
        has_rb = policy.rollback_plan is not None
        self.items.append(
            ChecklistItem(
                question="What is the rollback plan?",
                status="pass" if has_rb else "warn",
                detail=policy.rollback_plan.trigger if has_rb else "No rollback plan defined",
            )
        )

        # 8. Eval / shadow test
        self.items.append(
            ChecklistItem(
                question="What eval or shadow test is required before activation?",
                status="pending",
                detail="Shadow evaluation period recommended before active_enforced",
            )
        )

        # 9. Owner
        self.items.append(
            ChecklistItem(
                question="Who owns this policy?",
                status="pass" if policy.owner else "fail",
                detail=policy.owner.owner_id if policy.owner else "No owner assigned",
            )
        )

        # Overall readiness from gate
        self.overall_ready = gate_result.is_ready

        return self

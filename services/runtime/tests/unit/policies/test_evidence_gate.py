"""Unit tests for Policy Evidence Gate + Review Checklist (Phase 5.4)."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from domains.policies.models import (
    PolicyRecord,
    PolicyScope,
    PolicyState,
    PolicyRisk,
    PolicyEvidenceRef,
    PolicyRollbackPlan,
    PolicyOwner,
    EvidenceFreshness,
)
from domains.policies.evidence_gate import (
    PolicyEvidenceGate,
    PolicyReviewChecklist,
    ReadinessLevel,
    EvidenceGateResult,
)


# ── Helpers ──────────────────────────────────────────────────────────


def _make_policy(
    policy_id: str = "POL-001",
    state: PolicyState = PolicyState.DRAFT,
    evidence_refs: tuple[PolicyEvidenceRef, ...] = (),
    owner: PolicyOwner | None = None,
    rollback_plan: PolicyRollbackPlan | None = None,
    **kwargs,
) -> PolicyRecord:
    return PolicyRecord(
        policy_id=policy_id,
        title="Test Policy",
        scope=kwargs.pop("scope", PolicyScope.CORE),
        state=state,
        risk=kwargs.pop("risk", PolicyRisk.LOW),
        evidence_refs=evidence_refs,
        owner=owner,
        rollback_plan=rollback_plan,
        version=1,
        created_at=datetime.now(timezone.utc),
        **kwargs,
    )


def _make_evidence(
    ref_type: str = "candidate_rule", freshness: EvidenceFreshness = EvidenceFreshness.CURRENT
) -> PolicyEvidenceRef:
    return PolicyEvidenceRef(ref_type=ref_type, ref_id=f"{ref_type}:001", freshness=freshness)


def _make_owner() -> PolicyOwner:
    return PolicyOwner(owner_id="alice")


def _make_rollback() -> PolicyRollbackPlan:
    return PolicyRollbackPlan(
        trigger="false_positive_rate > 5%",
        authorized_by="alice",
        method="state_transition",
        blast_radius="CI gate",
        target_recovery_time="seconds",
    )


gate = PolicyEvidenceGate()


# ══════════════════════════════════════════════════════════════════════
# Draft with no evidence → NOT_READY
# ══════════════════════════════════════════════════════════════════════


def test_no_evidence_is_not_ready():
    policy = _make_policy()
    result = gate.assess(policy)
    assert result.level == ReadinessLevel.NOT_READY
    assert any("evidence" in r.lower() for r in result.reasons)


# ══════════════════════════════════════════════════════════════════════
# Draft with stale evidence → NOT_READY
# ══════════════════════════════════════════════════════════════════════


def test_stale_evidence_is_not_ready():
    policy = _make_policy(
        evidence_refs=(_make_evidence(freshness=EvidenceFreshness.STALE),),
    )
    result = gate.assess(policy)
    assert result.level == ReadinessLevel.NOT_READY
    assert any("stale" in r.lower() for r in result.reasons)


# ══════════════════════════════════════════════════════════════════════
# Draft with current evidence → READY_FOR_REVIEW (no owner/rollback yet)
# ══════════════════════════════════════════════════════════════════════


def test_current_evidence_ready_for_review():
    policy = _make_policy(
        evidence_refs=(_make_evidence(),),
    )
    result = gate.assess(policy)
    assert result.level == ReadinessLevel.READY_FOR_REVIEW
    assert any("owner" in r.lower() for r in result.reasons)


# ══════════════════════════════════════════════════════════════════════
# Single weak evidence → warning but may be review-ready
# ══════════════════════════════════════════════════════════════════════


def test_single_ci_artifact_has_warning():
    policy = _make_policy(
        evidence_refs=(_make_evidence(ref_type="ci_artifact"),),
    )
    result = gate.assess(policy)
    assert result.level == ReadinessLevel.READY_FOR_REVIEW
    assert any("ci_artifact" in w for w in result.warnings)


# ══════════════════════════════════════════════════════════════════════
# Strong evidence + owner + rollback → READY_FOR_ACTIVATION
# ══════════════════════════════════════════════════════════════════════


def test_full_evidence_owner_rollback_is_activation_ready():
    policy = _make_policy(
        evidence_refs=(
            _make_evidence(ref_type="candidate_rule"),
            _make_evidence(ref_type="lesson"),
            _make_evidence(ref_type="review"),
        ),
        owner=_make_owner(),
        rollback_plan=_make_rollback(),
    )
    result = gate.assess(policy)
    assert result.level == ReadinessLevel.READY_FOR_HUMAN_ACTIVATION_REVIEW


# ══════════════════════════════════════════════════════════════════════
# Evidence + owner + rollback but weak solo → READY_FOR_SHADOW
# ══════════════════════════════════════════════════════════════════════


def test_single_weak_evidence_with_owner_rollback_is_shadow_only():
    policy = _make_policy(
        evidence_refs=(_make_evidence(ref_type="ci_artifact"),),
        owner=_make_owner(),
        rollback_plan=_make_rollback(),
    )
    result = gate.assess(policy)
    assert result.level == ReadinessLevel.READY_FOR_SHADOW


# ══════════════════════════════════════════════════════════════════════
# Missing scope / risk → NOT_READY
# ══════════════════════════════════════════════════════════════════════


def test_missing_scope_fails():
    policy = _make_policy(scope=None, evidence_refs=(_make_evidence(),))
    result = gate.assess(policy)
    assert result.level == ReadinessLevel.NOT_READY
    assert any("scope" in r.lower() for r in result.reasons)


def test_missing_risk_fails():
    policy = _make_policy(risk=None, evidence_refs=(_make_evidence(),))
    result = gate.assess(policy)
    assert result.level == ReadinessLevel.NOT_READY
    assert any("risk" in r.lower() for r in result.reasons)


# ══════════════════════════════════════════════════════════════════════
# CodeQL finding alone → NOT activation-ready
# ══════════════════════════════════════════════════════════════════════


def test_codeql_finding_alone_is_not_activation_ready():
    policy = _make_policy(
        evidence_refs=(_make_evidence(ref_type="ci_artifact"),),
        owner=_make_owner(),
        rollback_plan=_make_rollback(),
    )
    result = gate.assess(policy)
    assert result.level != ReadinessLevel.READY_FOR_HUMAN_ACTIVATION_REVIEW
    assert any("ci_artifact" in w for w in result.warnings)


# ══════════════════════════════════════════════════════════════════════
# Accepted CandidateRule lineage → review ready
# ══════════════════════════════════════════════════════════════════════


def test_candidate_rule_lineage_supports_review():
    policy = _make_policy(
        evidence_refs=(
            _make_evidence(ref_type="candidate_rule"),
            _make_evidence(ref_type="lesson"),
        ),
    )
    result = gate.assess(policy)
    assert result.level == ReadinessLevel.READY_FOR_REVIEW
    assert result.is_ready


# ══════════════════════════════════════════════════════════════════════
# No active policy is produced by evidence gate
# ══════════════════════════════════════════════════════════════════════


def test_evidence_gate_does_not_produce_active_policy():
    """The evidence gate is read-only. It must not modify state."""
    policy = _make_policy(
        state=PolicyState.DRAFT,
        evidence_refs=(_make_evidence(),),
        owner=_make_owner(),
        rollback_plan=_make_rollback(),
    )
    original_state = policy.state
    gate.assess(policy)
    assert policy.state == original_state
    assert policy.state == PolicyState.DRAFT


# ══════════════════════════════════════════════════════════════════════
# Unknown ref_type → NOT_READY
# ══════════════════════════════════════════════════════════════════════


def test_unknown_ref_type_fails():
    policy = _make_policy(
        evidence_refs=(PolicyEvidenceRef(ref_type="codeql_alert", ref_id="CA-001"),),
    )
    result = gate.assess(policy)
    assert result.level == ReadinessLevel.NOT_READY
    assert any("codeql_alert" in r for r in result.reasons)


# ══════════════════════════════════════════════════════════════════════
# Regenerated evidence → valid
# ══════════════════════════════════════════════════════════════════════


def test_regenerated_evidence_is_valid():
    policy = _make_policy(
        evidence_refs=(_make_evidence(freshness=EvidenceFreshness.REGENERATED),),
    )
    result = gate.assess(policy)
    assert result.level == ReadinessLevel.READY_FOR_REVIEW


# ══════════════════════════════════════════════════════════════════════
# All stale → NOT_READY
# ══════════════════════════════════════════════════════════════════════


def test_all_stale_is_not_ready():
    policy = _make_policy(
        evidence_refs=(
            _make_evidence(freshness=EvidenceFreshness.STALE),
            _make_evidence(ref_type="lesson", freshness=EvidenceFreshness.STALE),
        ),
    )
    result = gate.assess(policy)
    assert result.level == ReadinessLevel.NOT_READY


# ══════════════════════════════════════════════════════════════════════
# Mixed fresh + stale → NOT_READY
# ══════════════════════════════════════════════════════════════════════


def test_mixed_fresh_and_stale_is_not_ready():
    policy = _make_policy(
        evidence_refs=(
            _make_evidence(freshness=EvidenceFreshness.CURRENT),
            _make_evidence(ref_type="lesson", freshness=EvidenceFreshness.STALE),
        ),
    )
    result = gate.assess(policy)
    assert result.level == ReadinessLevel.NOT_READY


# ══════════════════════════════════════════════════════════════════════
# Human exception evidence → treated as current
# ══════════════════════════════════════════════════════════════════════


def test_human_exception_not_counted_as_fresh():
    """Human exception is not CURRENT or REGENERATED.
    If all evidence is human_exception, there are no CURRENT/REGENERATED refs."""
    policy = _make_policy(
        evidence_refs=(_make_evidence(freshness=EvidenceFreshness.HUMAN_EXCEPTION),),
    )
    result = gate.assess(policy)
    assert result.level == ReadinessLevel.NOT_READY
    assert any("fresh" in r.lower() or "CURRENT" in r for r in result.reasons)


# ══════════════════════════════════════════════════════════════════════
# Review Checklist Tests
# ══════════════════════════════════════════════════════════════════════


def test_checklist_builds_all_items():
    policy = _make_policy(
        evidence_refs=(
            _make_evidence(ref_type="candidate_rule"),
            _make_evidence(ref_type="lesson"),
        ),
        owner=_make_owner(),
        rollback_plan=_make_rollback(),
    )
    result = gate.assess(policy)
    checklist = PolicyReviewChecklist(policy_id="").build(policy, result)
    assert len(checklist.items) == 9
    assert checklist.overall_ready


def test_checklist_with_no_evidence():
    policy = _make_policy()
    result = gate.assess(policy)
    checklist = PolicyReviewChecklist(policy_id="").build(policy, result)
    assert not checklist.overall_ready


def test_checklist_no_owner_flagged():
    policy = _make_policy(
        evidence_refs=(_make_evidence(),),
    )
    result = gate.assess(policy)
    checklist = PolicyReviewChecklist(policy_id="").build(policy, result)
    owner_item = next(i for i in checklist.items if "owns" in i.question)
    assert owner_item.status == "fail"


def test_checklist_has_shadow_test_question():
    policy = _make_policy(
        evidence_refs=(_make_evidence(),),
    )
    result = gate.assess(policy)
    checklist = PolicyReviewChecklist(policy_id="").build(policy, result)
    shadow_item = next(i for i in checklist.items if "shadow" in i.question)
    assert shadow_item.status == "pending"


def test_checklist_stale_evidence_flagged():
    policy = _make_policy(
        evidence_refs=(_make_evidence(freshness=EvidenceFreshness.STALE),),
    )
    result = gate.assess(policy)
    checklist = PolicyReviewChecklist(policy_id="").build(policy, result)
    fresh_item = next(i for i in checklist.items if "fresh" in i.question)
    assert fresh_item.status == "fail"


# ══════════════════════════════════════════════════════════════════════
# ReadinessLevel transitions: only allowed levels
# ══════════════════════════════════════════════════════════════════════


def test_not_ready_has_no_false_positive_on_empty():
    """A policy with no evidence but valid scope/risk should still be NOT_READY."""
    policy = _make_policy(scope=PolicyScope.CORE, risk=PolicyRisk.LOW)
    result = gate.assess(policy)
    assert result.level == ReadinessLevel.NOT_READY
    assert not result.is_ready


# ══════════════════════════════════════════════════════════════════════
# EvidenceGateResult properties
# ══════════════════════════════════════════════════════════════════════


def test_result_is_ready_property():
    assert not EvidenceGateResult(level=ReadinessLevel.NOT_READY).is_ready
    assert EvidenceGateResult(level=ReadinessLevel.READY_FOR_REVIEW).is_ready
    assert EvidenceGateResult(level=ReadinessLevel.READY_FOR_SHADOW).is_ready
    assert EvidenceGateResult(level=ReadinessLevel.READY_FOR_HUMAN_ACTIVATION_REVIEW).is_ready

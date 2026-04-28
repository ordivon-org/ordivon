"""Policy Approval Gate + Rollback Contract tests (Phase 5.6)."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

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
from domains.policies.approval import (
    PolicyApprovalGate,
    PolicyApprovalRequest,
    PolicyRollbackContract,
    ApprovalOutcome,
    Reviewer,
    ReviewerRole,
)
from domains.policies.evidence_gate import ReadinessLevel
from domains.policies.shadow import ShadowVerdict


def _make_evidence(ref_type="candidate_rule", freshness=EvidenceFreshness.CURRENT) -> PolicyEvidenceRef:
    return PolicyEvidenceRef(ref_type=ref_type, ref_id=f"{ref_type}:001", freshness=freshness)


def _make_owner() -> PolicyOwner:
    return PolicyOwner(owner_id="alice")


def _make_rollback_plan() -> PolicyRollbackPlan:
    return PolicyRollbackPlan(
        trigger="fp_rate > 5%",
        authorized_by="alice",
        method="state_transition",
        blast_radius="CI gate",
        target_recovery_time="seconds",
    )


def _make_contract() -> PolicyRollbackContract:
    return PolicyRollbackContract(
        trigger="fp_rate > 5%",
        authorized_by="alice",
        method="state_transition",
        blast_radius="CI gate",
        target_recovery_time="seconds",
        post_rollback_reviewer="bob",
    )


def _make_policy(**kwargs) -> PolicyRecord:
    defaults = {
        "policy_id": "POL-APP-001",
        "title": "Approval Test Policy",
        "scope": PolicyScope.SECURITY,
        "state": PolicyState.DRAFT,
        "risk": PolicyRisk.LOW,
        "evidence_refs": (),
        "version": 1,
        "created_at": datetime.now(timezone.utc),
    }
    defaults.update(kwargs)
    return PolicyRecord(**defaults)


def _make_request(policy=None, **kwargs) -> PolicyApprovalRequest:
    if policy is None:
        policy = _make_policy(evidence_refs=(_make_evidence(),), owner=_make_owner())
    defaults = {
        "policy": policy,
        "evidence_readiness": ReadinessLevel.READY_FOR_ACTIVATION,
        "shadow_summary": "All shadow cases passed.",
        "shadow_verdicts": (ShadowVerdict.WOULD_RECOMMEND_MERGE, ShadowVerdict.WOULD_EXECUTE),
        "reviewers": (Reviewer("alice", ReviewerRole.TECHNICAL_REVIEWER),),
        "rollback_contract": _make_contract(),
    }
    defaults.update(kwargs)
    return PolicyApprovalRequest(**defaults)


gate = PolicyApprovalGate()


# ══════════════════════════════════════════════════════════════════════
# Low-risk policy with full evidence → approved_for_shadow
# ══════════════════════════════════════════════════════════════════════


def test_low_risk_full_evidence_approved_for_shadow():
    request = _make_request()
    decision = gate.review(request)
    assert decision.outcome == ApprovalOutcome.APPROVED_FOR_SHADOW
    assert "shadow evaluation" in decision.rationale.lower()


# ══════════════════════════════════════════════════════════════════════
# Missing owner → rejected
# ══════════════════════════════════════════════════════════════════════


def test_missing_owner_rejected():
    policy = _make_policy(evidence_refs=(_make_evidence(),))
    request = _make_request(policy=policy)
    decision = gate.review(request)
    assert decision.outcome == ApprovalOutcome.REJECTED
    assert "owner" in decision.rationale.lower()


# ══════════════════════════════════════════════════════════════════════
# Missing rollback contract → rejected
# ══════════════════════════════════════════════════════════════════════


def test_missing_rollback_contract_rejected():
    request = _make_request(rollback_contract=None)
    decision = gate.review(request)
    assert decision.outcome == ApprovalOutcome.REJECTED
    assert "rollback" in decision.rationale.lower()


# ══════════════════════════════════════════════════════════════════════
# Stale evidence → needs_more_evidence
# ══════════════════════════════════════════════════════════════════════


def test_stale_evidence_needs_more_evidence():
    policy = _make_policy(
        evidence_refs=(_make_evidence(freshness=EvidenceFreshness.STALE),),
        owner=_make_owner(),
    )
    request = _make_request(
        policy=policy,
        evidence_readiness=ReadinessLevel.NOT_READY,
    )
    decision = gate.review(request)
    assert decision.outcome == ApprovalOutcome.NEEDS_MORE_EVIDENCE


# ══════════════════════════════════════════════════════════════════════
# All-stale evidence → needs_more_evidence (even if gate says ready)
# ══════════════════════════════════════════════════════════════════════


def test_all_stale_evidence_needs_more():
    policy = _make_policy(
        evidence_refs=(
            _make_evidence(freshness=EvidenceFreshness.STALE),
            _make_evidence("lesson", freshness=EvidenceFreshness.STALE),
        ),
        owner=_make_owner(),
    )
    request = _make_request(policy=policy)
    decision = gate.review(request)
    assert decision.outcome == ApprovalOutcome.NEEDS_MORE_EVIDENCE
    assert "stale" in decision.rationale.lower()


# ══════════════════════════════════════════════════════════════════════
# Shadow WOULD_HOLD → needs_more_shadow
# ══════════════════════════════════════════════════════════════════════


def test_shadow_would_hold_needs_more_shadow():
    request = _make_request(
        shadow_verdicts=(ShadowVerdict.WOULD_HOLD,),
    )
    decision = gate.review(request)
    assert decision.outcome == ApprovalOutcome.NEEDS_MORE_SHADOW
    assert any("hold" in c.lower() for c in decision.conditions)


# ══════════════════════════════════════════════════════════════════════
# Shadow WOULD_REJECT → rejected
# ══════════════════════════════════════════════════════════════════════


def test_shadow_would_reject_rejected():
    request = _make_request(
        shadow_verdicts=(ShadowVerdict.WOULD_RECOMMEND_MERGE, ShadowVerdict.WOULD_REJECT),
    )
    decision = gate.review(request)
    assert decision.outcome == ApprovalOutcome.REJECTED
    assert "reject" in decision.rationale.lower()


# ══════════════════════════════════════════════════════════════════════
# High risk without governance reviewer → rejected
# ══════════════════════════════════════════════════════════════════════


def test_high_risk_without_gov_reviewer_rejected():
    policy = _make_policy(
        risk=PolicyRisk.HIGH,
        evidence_refs=(_make_evidence(),),
        owner=_make_owner(),
    )
    request = _make_request(policy=policy)
    decision = gate.review(request)
    assert decision.outcome == ApprovalOutcome.REJECTED
    assert "governance" in decision.rationale.lower()


# ══════════════════════════════════════════════════════════════════════
# Medium risk without governance reviewer → rejected
# ══════════════════════════════════════════════════════════════════════


def test_medium_risk_without_gov_reviewer_rejected():
    policy = _make_policy(
        risk=PolicyRisk.MEDIUM,
        evidence_refs=(_make_evidence(),),
        owner=_make_owner(),
    )
    request = _make_request(policy=policy)
    decision = gate.review(request)
    assert decision.outcome == ApprovalOutcome.REJECTED
    assert "governance" in decision.rationale.lower()


# ══════════════════════════════════════════════════════════════════════
# High risk WITH governance reviewer → approved_for_shadow
# ══════════════════════════════════════════════════════════════════════


def test_high_risk_with_gov_reviewer_approved():
    policy = _make_policy(
        risk=PolicyRisk.HIGH,
        evidence_refs=(_make_evidence(),),
        owner=_make_owner(),
    )
    request = _make_request(
        policy=policy,
        reviewers=(
            Reviewer("alice", ReviewerRole.TECHNICAL_REVIEWER),
            Reviewer("bob", ReviewerRole.GOVERNANCE_REVIEWER),
        ),
    )
    decision = gate.review(request)
    assert decision.outcome == ApprovalOutcome.APPROVED_FOR_SHADOW


# ══════════════════════════════════════════════════════════════════════
# active_enforced request → deferred
# ══════════════════════════════════════════════════════════════════════


def test_active_enforced_request_deferred():
    request = _make_request(requested_outcome="active_enforced")
    decision = gate.review(request)
    assert decision.outcome == ApprovalOutcome.DEFERRED
    assert "deferred" in decision.rationale.lower() or "Only 'approved_for_shadow'" in decision.rationale


# ══════════════════════════════════════════════════════════════════════
# Approval gate never mutates PolicyRecord
# ══════════════════════════════════════════════════════════════════════


def test_approval_gate_never_mutates_policy():
    policy = _make_policy(
        evidence_refs=(_make_evidence(),),
        owner=_make_owner(),
        state=PolicyState.DRAFT,
    )
    original = policy.state
    request = _make_request(policy=policy)
    gate.review(request)
    assert policy.state == original
    assert policy.state == PolicyState.DRAFT


# ══════════════════════════════════════════════════════════════════════
# No reviewers → rejected
# ══════════════════════════════════════════════════════════════════════


def test_no_reviewers_rejected():
    request = _make_request(reviewers=())
    decision = gate.review(request)
    assert decision.outcome == ApprovalOutcome.REJECTED


# ══════════════════════════════════════════════════════════════════════
# Rollback Contract Tests
# ══════════════════════════════════════════════════════════════════════


def test_rollback_contract_validates_trigger():
    with pytest.raises(ValueError, match="trigger"):
        PolicyRollbackContract(
            trigger="",
            authorized_by="a",
            method="m",
            blast_radius="b",
            target_recovery_time="t",
            post_rollback_reviewer="r",
        )


def test_rollback_contract_validates_authorized_by():
    with pytest.raises(ValueError, match="authorized_by"):
        PolicyRollbackContract(
            trigger="t",
            authorized_by="",
            method="m",
            blast_radius="b",
            target_recovery_time="t",
            post_rollback_reviewer="r",
        )


def test_rollback_contract_validates_method():
    with pytest.raises(ValueError, match="method"):
        PolicyRollbackContract(
            trigger="t",
            authorized_by="a",
            method="",
            blast_radius="b",
            target_recovery_time="t",
            post_rollback_reviewer="r",
        )


def test_rollback_contract_validates_blast_radius():
    with pytest.raises(ValueError, match="blast_radius"):
        PolicyRollbackContract(
            trigger="t",
            authorized_by="a",
            method="m",
            blast_radius="",
            target_recovery_time="t",
            post_rollback_reviewer="r",
        )


def test_rollback_contract_validates_recovery_time():
    with pytest.raises(ValueError, match="target_recovery_time"):
        PolicyRollbackContract(
            trigger="t",
            authorized_by="a",
            method="m",
            blast_radius="b",
            target_recovery_time="",
            post_rollback_reviewer="r",
        )


def test_rollback_contract_requires_post_reviewer():
    with pytest.raises(ValueError, match="post_rollback_reviewer"):
        PolicyRollbackContract(
            trigger="t",
            authorized_by="a",
            method="m",
            blast_radius="b",
            target_recovery_time="t",
            post_rollback_review_required=True,
            post_rollback_reviewer="",
        )


def test_rollback_contract_from_plan():
    plan = _make_rollback_plan()
    contract = PolicyRollbackContract.from_rollback_plan(plan, post_rollback_reviewer="bob")
    assert contract.trigger == plan.trigger
    assert contract.authorized_by == plan.authorized_by
    assert contract.post_rollback_reviewer == "bob"


def test_reviewer_requires_id():
    with pytest.raises(ValueError, match="reviewer_id"):
        Reviewer(reviewer_id="", role=ReviewerRole.TECHNICAL_REVIEWER)


# ══════════════════════════════════════════════════════════════════════
# ApprovalDecision is immutable
# ══════════════════════════════════════════════════════════════════════


def test_approval_decision_is_frozen():
    decision = gate.review(_make_request())
    assert decision.outcome == ApprovalOutcome.APPROVED_FOR_SHADOW
    with pytest.raises(Exception):
        decision.outcome = ApprovalOutcome.REJECTED  # type: ignore[misc]

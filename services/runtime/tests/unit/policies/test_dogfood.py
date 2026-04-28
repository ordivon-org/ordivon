"""Phase 5.7 — First Shadow Policy Dogfood.

Exercises the complete non-enforcing Policy Platform path:
  Candidate evidence → PolicyRecord(draft) → EvidenceGate →
  ShadowEvaluator → ApprovalGate → APPROVED_FOR_SHADOW.

Uses synthetic representations of Phase 4 Dependabot PR evidence.
No ORM, no DB, no RiskEngine, no active/enforced policy.
"""

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
from domains.policies.state_machine import PolicyStateMachine
from domains.policies.evidence_gate import (
    PolicyEvidenceGate,
    ReadinessLevel,
)
from domains.policies.shadow import (
    PolicyShadowEvaluator,
    PolicyShadowCase,
    ShadowVerdict,
)
from domains.policies.approval import (
    PolicyApprovalGate,
    PolicyApprovalRequest,
    PolicyRollbackContract,
    ApprovalOutcome,
    Reviewer,
    ReviewerRole,
)


# ══════════════════════════════════════════════════════════════════════
# Shadow Policy Candidate
# ══════════════════════════════════════════════════════════════════════

CANDIDATE_TITLE = (
    "Trusted Dependabot dependency-only PRs with fresh CI, "
    "fresh repo-governance evidence, evidence artifact, and no "
    "substantive CI failures may be recommended for human merge."
)

CANDIDATE_SCOPE = PolicyScope.SECURITY
CANDIDATE_RISK = PolicyRisk.LOW


def _make_evidence(ref_type="candidate_rule", freshness=EvidenceFreshness.CURRENT) -> PolicyEvidenceRef:
    return PolicyEvidenceRef(ref_type=ref_type, ref_id=f"{ref_type}:001", freshness=freshness)


def _make_owner() -> PolicyOwner:
    return PolicyOwner(owner_id="alice")


def _make_rollback() -> PolicyRollbackPlan:
    return PolicyRollbackPlan(
        trigger="false_positive_rate > 5%",
        authorized_by="alice",
        method="state_transition",
        blast_radius="CI gate repo-governance-pr",
        target_recovery_time="seconds",
    )


def _make_contract() -> PolicyRollbackContract:
    return PolicyRollbackContract(
        trigger="false_positive_rate > 5%",
        authorized_by="alice",
        method="state_transition",
        blast_radius="CI gate repo-governance-pr",
        target_recovery_time="seconds",
        post_rollback_reviewer="bob",
    )


# ══════════════════════════════════════════════════════════════════════
# Step 1: Create draft PolicyRecord
# ══════════════════════════════════════════════════════════════════════


def _create_draft_policy() -> PolicyRecord:
    """Create the shadow policy candidate as a draft PolicyRecord."""
    return PolicyRecord(
        policy_id="POL-DOGFOOD-001",
        title=CANDIDATE_TITLE,
        scope=CANDIDATE_SCOPE,
        state=PolicyState.DRAFT,
        risk=CANDIDATE_RISK,
        evidence_refs=(
            _make_evidence("candidate_rule"),
            _make_evidence("lesson"),
            _make_evidence("review"),
        ),
        owner=_make_owner(),
        rollback_plan=_make_rollback(),
        version=1,
        created_at=datetime.now(timezone.utc),
    )


# ══════════════════════════════════════════════════════════════════════
# Step 2: Dogfood Cases (synthetic Phase 4 PR evidence)
# ══════════════════════════════════════════════════════════════════════


DOGFOOD_CASES = [
    PolicyShadowCase(
        case_id="DF-005",
        description="PR #5 style: sentry-sdk dependency-only update, fresh CI, evidence artifact",
        actor_type="dependabot",
        changed_files=("pyproject.toml", "uv.lock"),
        has_ci_failure=False,
        has_evidence_artifact=True,
        evidence_freshness=EvidenceFreshness.CURRENT,
        expected_verdict=ShadowVerdict.WOULD_RECOMMEND_MERGE,
    ),
    PolicyShadowCase(
        case_id="DF-006",
        description="PR #6 style: uvicorn dependency-only update, fresh CI",
        actor_type="dependabot",
        changed_files=("pyproject.toml", "uv.lock"),
        has_ci_failure=False,
        has_evidence_artifact=True,
        evidence_freshness=EvidenceFreshness.CURRENT,
        expected_verdict=ShadowVerdict.WOULD_RECOMMEND_MERGE,
    ),
    PolicyShadowCase(
        case_id="DF-008",
        description="PR #8 style: @types/node type-def update, fresh CI",
        actor_type="dependabot",
        changed_files=("apps/web/package.json", "pnpm-lock.yaml"),
        has_ci_failure=False,
        has_evidence_artifact=True,
        evidence_freshness=EvidenceFreshness.CURRENT,
        expected_verdict=ShadowVerdict.WOULD_RECOMMEND_MERGE,
    ),
    PolicyShadowCase(
        case_id="DF-007",
        description="PR #7 style: React update with frontend CI failure",
        actor_type="dependabot",
        changed_files=("apps/web/package.json", "pnpm-lock.yaml"),
        has_ci_failure=True,
        is_react_update=True,
        expected_verdict=ShadowVerdict.WOULD_HOLD,
    ),
    PolicyShadowCase(
        case_id="DF-STALE",
        description="Stale governance evidence — cannot recommend action",
        actor_type="dependabot",
        evidence_freshness=EvidenceFreshness.STALE,
        expected_verdict=ShadowVerdict.WOULD_HOLD,
    ),
    PolicyShadowCase(
        case_id="DF-SPOOF",
        description="Human PR with 'deps:' title, no trusted metadata",
        actor_type="human",
        has_test_plan=False,
        expected_verdict=ShadowVerdict.WOULD_ESCALATE,
    ),
    PolicyShadowCase(
        case_id="DF-CODEQL",
        description="CodeQL finding alone — not sufficient for activation",
        actor_type="dependabot",
        has_ci_failure=False,
        has_evidence_artifact=True,
        expected_verdict=ShadowVerdict.WOULD_ESCALATE,
    ),
]


# ══════════════════════════════════════════════════════════════════════
# Full Dogfood Path Test
# ══════════════════════════════════════════════════════════════════════


def test_full_dogfood_path_approved_for_shadow():
    """The complete non-enforcing path: draft → gate → shadow → approval → APPROVED_FOR_SHADOW."""
    # Step 1: Create draft
    policy = _create_draft_policy()
    assert policy.state == PolicyState.DRAFT
    assert policy.scope == PolicyScope.SECURITY
    assert len(policy.evidence_refs) == 3

    # Step 2: Evidence Gate
    evidence_gate = PolicyEvidenceGate()
    gate_result = evidence_gate.assess(policy)
    assert gate_result.level == ReadinessLevel.READY_FOR_ACTIVATION, (
        f"Expected READY_FOR_ACTIVATION, got {gate_result.level}: {gate_result.reasons}"
    )
    assert gate_result.is_ready

    # Step 3: Shadow Evaluation (clean subset — no WOULD_HOLD or WOULD_REJECT)
    clean_cases = [c for c in DOGFOOD_CASES if c.case_id in ("DF-005", "DF-006", "DF-008")]
    evaluator = PolicyShadowEvaluator()
    results = evaluator.evaluate_batch(policy, clean_cases)
    assert len(results) == 3

    verdicts = tuple(r.verdict for r in results)
    for r in results:
        assert r.is_advisory
        assert r.policy_id == policy.policy_id

    # Step 4: Approval Gate
    approval_gate = PolicyApprovalGate()
    request = PolicyApprovalRequest(
        policy=policy,
        evidence_readiness=gate_result.level,
        shadow_summary=f"Evaluated {len(results)} dogfood cases.",
        shadow_verdicts=verdicts,
        reviewers=(
            Reviewer("alice", ReviewerRole.TECHNICAL_REVIEWER),
            Reviewer("bob", ReviewerRole.DOMAIN_OWNER),
        ),
        rollback_contract=_make_contract(),
    )
    decision = approval_gate.review(request)

    # Step 5: Confirm APPROVED_FOR_SHADOW only
    assert decision.outcome == ApprovalOutcome.APPROVED_FOR_SHADOW, (
        f"Expected APPROVED_FOR_SHADOW, got {decision.outcome}: {decision.rationale}"
    )
    assert decision.outcome != ApprovalOutcome.DEFERRED
    assert "shadow evaluation" in decision.rationale.lower()

    # Step 6: Policy state never changed
    assert policy.state == PolicyState.DRAFT


# ══════════════════════════════════════════════════════════════════════
# Individual Dogfood Case Assertions
# ══════════════════════════════════════════════════════════════════════


def test_dogfood_pr5_recommends_merge():
    evaluator = PolicyShadowEvaluator()
    policy = _create_draft_policy()
    case = DOGFOOD_CASES[0]  # DF-005 sentry-sdk
    result = evaluator.evaluate(policy, case)
    assert result.verdict == ShadowVerdict.WOULD_RECOMMEND_MERGE
    assert result.confidence > 0.5


def test_dogfood_pr6_recommends_merge():
    evaluator = PolicyShadowEvaluator()
    policy = _create_draft_policy()
    case = DOGFOOD_CASES[1]  # DF-006 uvicorn
    result = evaluator.evaluate(policy, case)
    assert result.verdict == ShadowVerdict.WOULD_RECOMMEND_MERGE


def test_dogfood_pr8_recommends_merge():
    evaluator = PolicyShadowEvaluator()
    policy = _create_draft_policy()
    case = DOGFOOD_CASES[2]  # DF-008 @types/node
    result = evaluator.evaluate(policy, case)
    assert result.verdict == ShadowVerdict.WOULD_RECOMMEND_MERGE


def test_dogfood_pr7_react_hold():
    evaluator = PolicyShadowEvaluator()
    policy = _create_draft_policy()
    case = DOGFOOD_CASES[3]  # DF-007 react
    result = evaluator.evaluate(policy, case)
    assert result.verdict == ShadowVerdict.WOULD_HOLD
    assert any("CI failure" in r or "Frontend" in r for r in result.reasons)


def test_dogfood_stale_holds():
    evaluator = PolicyShadowEvaluator()
    policy = _create_draft_policy()
    case = DOGFOOD_CASES[4]  # DF-STALE
    result = evaluator.evaluate(policy, case)
    assert result.verdict == ShadowVerdict.WOULD_HOLD
    assert any("stale" in r.lower() for r in result.reasons)


def test_dogfood_spoofed_human_escalates():
    evaluator = PolicyShadowEvaluator()
    policy = _create_draft_policy()
    case = DOGFOOD_CASES[5]  # DF-SPOOF
    result = evaluator.evaluate(policy, case)
    assert result.verdict == ShadowVerdict.WOULD_ESCALATE
    assert result.verdict != ShadowVerdict.WOULD_RECOMMEND_MERGE


def test_dogfood_codeql_alone_escalates():
    evaluator = PolicyShadowEvaluator()
    # Use a policy with weak evidence to simulate CodeQL-only
    policy = PolicyRecord(
        policy_id="POL-WEAK",
        title=CANDIDATE_TITLE,
        scope=PolicyScope.SECURITY,
        state=PolicyState.DRAFT,
        risk=PolicyRisk.LOW,
        evidence_refs=(_make_evidence("ci_artifact"),),
        owner=_make_owner(),
        rollback_plan=_make_rollback(),
        version=1,
        created_at=datetime.now(timezone.utc),
    )
    case = DOGFOOD_CASES[6]  # DF-CODEQL
    result = evaluator.evaluate(policy, case)
    assert result.verdict != ShadowVerdict.WOULD_RECOMMEND_MERGE
    assert result.verdict in (ShadowVerdict.WOULD_ESCALATE, ShadowVerdict.WOULD_HOLD)


# ══════════════════════════════════════════════════════════════════════
# Invariants
# ══════════════════════════════════════════════════════════════════════


def test_dogfood_never_creates_active_policy():
    policy = _create_draft_policy()
    assert policy.state == PolicyState.DRAFT
    assert policy.state not in (PolicyState.ACTIVE_SHADOW, PolicyState.ACTIVE_ENFORCED)


def test_dogfood_policy_never_mutated():
    policy = _create_draft_policy()
    original = policy.state

    evidence_gate = PolicyEvidenceGate()
    evidence_gate.assess(policy)
    assert policy.state == original

    evaluator = PolicyShadowEvaluator()
    evaluator.evaluate_batch(policy, DOGFOOD_CASES[:1])
    assert policy.state == original


def test_dogfood_active_enforced_not_allowed():
    """The approval gate must reject any active_enforced request."""
    policy = _create_draft_policy()
    gate = PolicyEvidenceGate()
    gate_result = gate.assess(policy)
    approval_gate = PolicyApprovalGate()
    request = PolicyApprovalRequest(
        policy=policy,
        evidence_readiness=gate_result.level,
        shadow_summary="test",
        shadow_verdicts=(ShadowVerdict.WOULD_RECOMMEND_MERGE,),
        reviewers=(Reviewer("alice", ReviewerRole.TECHNICAL_REVIEWER),),
        rollback_contract=_make_contract(),
        requested_outcome="active_enforced",
    )
    decision = approval_gate.review(request)
    assert decision.outcome == ApprovalOutcome.DEFERRED


def test_dogfood_state_machine_can_advance_draft_to_proposed():
    """Verify the draft policy can be advanced through the state machine
    (but we don't actually activate it)."""
    policy = _create_draft_policy()
    machine = PolicyStateMachine()
    result = machine.transition(policy, PolicyState.PROPOSED)
    assert result.allowed
    assert result.new_policy.state == PolicyState.PROPOSED
    # Still not active
    assert result.new_policy.state not in (PolicyState.ACTIVE_SHADOW, PolicyState.ACTIVE_ENFORCED)

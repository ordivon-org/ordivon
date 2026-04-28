"""Shadow evaluation tests — red-team corpus + invariants (Phase 5.5)."""

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
from domains.policies.shadow import (
    PolicyShadowCase,
    PolicyShadowResult,
    PolicyShadowEvaluator,
    ShadowVerdict,
)
from domains.policies.evidence_gate import ReadinessLevel


def _make_policy(**kwargs) -> PolicyRecord:
    defaults = {
        "policy_id": "POL-SHADOW-001",
        "title": "Shadow Test Policy",
        "scope": PolicyScope.SECURITY,
        "state": PolicyState.DRAFT,
        "risk": PolicyRisk.LOW,
        "evidence_refs": (),
        "version": 1,
        "created_at": datetime.now(timezone.utc),
    }
    defaults.update(kwargs)
    return PolicyRecord(**defaults)


def _make_evidence(ref_type="candidate_rule", freshness=EvidenceFreshness.CURRENT) -> PolicyEvidenceRef:
    return PolicyEvidenceRef(ref_type=ref_type, ref_id=f"{ref_type}:001", freshness=freshness)


def _make_owner() -> PolicyOwner:
    return PolicyOwner(owner_id="alice")


def _make_rollback() -> PolicyRollbackPlan:
    return PolicyRollbackPlan(
        trigger="fp_rate > 5%",
        authorized_by="alice",
        method="state_transition",
        blast_radius="CI gate",
        target_recovery_time="seconds",
    )


evaluator = PolicyShadowEvaluator()


# ══════════════════════════════════════════════════════════════════════
# Red-Team Case 1: Trusted Dependabot + fresh CI → would_recommend_merge
# ══════════════════════════════════════════════════════════════════════


def test_dependabot_clean_pr_would_recommend_merge():
    policy = _make_policy(
        evidence_refs=(
            _make_evidence("candidate_rule"),
            _make_evidence("lesson"),
        ),
        owner=_make_owner(),
        rollback_plan=_make_rollback(),
    )
    case = PolicyShadowCase(
        case_id="RT-001",
        description="Dependabot dependency-only PR with fresh CI and evidence",
        actor_type="dependabot",
        changed_files=("pyproject.toml", "uv.lock"),
        has_ci_failure=False,
        has_evidence_artifact=True,
        evidence_freshness=EvidenceFreshness.CURRENT,
        expected_verdict=ShadowVerdict.WOULD_RECOMMEND_MERGE,
    )
    result = evaluator.evaluate(policy, case)
    assert result.verdict == ShadowVerdict.WOULD_RECOMMEND_MERGE
    assert result.confidence > 0.5
    assert result.is_advisory


# ══════════════════════════════════════════════════════════════════════
# Red-Team Case 2: Dependabot React + frontend CI failure → would_hold
# ══════════════════════════════════════════════════════════════════════


def test_dependabot_react_ci_failure_would_hold():
    policy = _make_policy(
        evidence_refs=(_make_evidence("candidate_rule"),),
        owner=_make_owner(),
        rollback_plan=_make_rollback(),
    )
    case = PolicyShadowCase(
        case_id="RT-002",
        description="Dependabot React update with frontend CI failure",
        actor_type="dependabot",
        changed_files=("apps/web/package.json", "pnpm-lock.yaml"),
        has_ci_failure=True,
        is_react_update=True,
        expected_verdict=ShadowVerdict.WOULD_HOLD,
    )
    result = evaluator.evaluate(policy, case)
    assert result.verdict == ShadowVerdict.WOULD_HOLD
    assert any("CI failure" in r or "Frontend" in r for r in result.reasons)


# ══════════════════════════════════════════════════════════════════════
# Red-Team Case 3: Stale evidence → would_hold (not recommend merge)
# ══════════════════════════════════════════════════════════════════════


def test_stale_evidence_would_hold():
    policy = _make_policy(
        evidence_refs=(_make_evidence("candidate_rule"),),
        owner=_make_owner(),
        rollback_plan=_make_rollback(),
    )
    case = PolicyShadowCase(
        case_id="RT-003",
        description="Dependabot PR with stale governance evidence",
        actor_type="dependabot",
        evidence_freshness=EvidenceFreshness.STALE,
        expected_verdict=ShadowVerdict.WOULD_HOLD,
    )
    result = evaluator.evaluate(policy, case)
    assert result.verdict == ShadowVerdict.WOULD_HOLD
    assert result.verdict != ShadowVerdict.WOULD_RECOMMEND_MERGE
    assert any("stale" in r.lower() for r in result.reasons)


# ══════════════════════════════════════════════════════════════════════
# Red-Team Case 4: Human "deps:" PR → no bot treatment
# ══════════════════════════════════════════════════════════════════════


def test_human_deps_title_pr_not_treated_as_bot():
    policy = _make_policy(
        evidence_refs=(_make_evidence("candidate_rule"),),
        owner=_make_owner(),
        rollback_plan=_make_rollback(),
    )
    case = PolicyShadowCase(
        case_id="RT-004",
        description="Human PR with 'deps:' title but no trusted metadata",
        actor_type="human",
        has_test_plan=False,
        expected_verdict=ShadowVerdict.WOULD_ESCALATE,
    )
    result = evaluator.evaluate(policy, case)
    assert result.verdict == ShadowVerdict.WOULD_ESCALATE
    assert result.verdict != ShadowVerdict.WOULD_RECOMMEND_MERGE
    assert any("bot" in r.lower() or "does not confer" in r.lower() for r in result.reasons)


# ══════════════════════════════════════════════════════════════════════
# Red-Team Case 5: CodeQL finding alone → no activation recommendation
# ══════════════════════════════════════════════════════════════════════


def test_codeql_finding_alone_no_activation():
    policy = _make_policy(
        evidence_refs=(_make_evidence("ci_artifact"),),  # weak solo
        owner=_make_owner(),
        rollback_plan=_make_rollback(),
    )
    case = PolicyShadowCase(
        case_id="RT-005",
        description="Policy based solely on CodeQL finding",
        actor_type="dependabot",
        expected_verdict=ShadowVerdict.WOULD_ESCALATE,
    )
    result = evaluator.evaluate(policy, case)
    # Evidence gate should flag this as not activation-ready
    assert result.verdict != ShadowVerdict.WOULD_RECOMMEND_MERGE
    assert result.verdict in (ShadowVerdict.WOULD_ESCALATE, ShadowVerdict.WOULD_HOLD)


# ══════════════════════════════════════════════════════════════════════
# Red-Team Case 6: Single event evidence → not enough for activation
# ══════════════════════════════════════════════════════════════════════


def test_single_event_evidence_not_activation_ready():
    policy = _make_policy(
        evidence_refs=(_make_evidence("ci_artifact"),),
        owner=_make_owner(),
        rollback_plan=_make_rollback(),
    )
    # Verify evidence gate result
    from domains.policies.evidence_gate import PolicyEvidenceGate

    gate = PolicyEvidenceGate()
    result = gate.assess(policy)
    assert result.level != ReadinessLevel.READY_FOR_HUMAN_ACTIVATION_REVIEW
    assert any("ci_artifact" in w for w in result.warnings)


# ══════════════════════════════════════════════════════════════════════
# Red-Team Case 7: Missing rollback plan → cannot become activation-ready
# ══════════════════════════════════════════════════════════════════════


def test_missing_rollback_plan_not_activation_ready():
    policy = _make_policy(
        evidence_refs=(
            _make_evidence("candidate_rule"),
            _make_evidence("lesson"),
            _make_evidence("review"),
        ),
        owner=_make_owner(),
        # no rollback_plan
    )
    from domains.policies.evidence_gate import PolicyEvidenceGate

    gate = PolicyEvidenceGate()
    result = gate.assess(policy)
    assert result.level != ReadinessLevel.READY_FOR_HUMAN_ACTIVATION_REVIEW
    # Without rollback_plan, even strong evidence only reaches READY_FOR_REVIEW
    assert result.level == ReadinessLevel.READY_FOR_REVIEW


# ══════════════════════════════════════════════════════════════════════
# Red-Team Case 8: Policy scope mismatch → no_match
# ══════════════════════════════════════════════════════════════════════


def test_scope_mismatch_returns_no_match():
    policy = _make_policy(scope=PolicyScope.SECURITY)
    case = PolicyShadowCase(
        case_id="RT-008",
        description="Finance case against security-scoped policy",
        actor_type="human",
        policy_scope=PolicyScope.PACK,
        expected_verdict=ShadowVerdict.NO_MATCH,
    )
    result = evaluator.evaluate(policy, case)
    assert result.verdict == ShadowVerdict.NO_MATCH
    assert result.confidence == 1.0


# ══════════════════════════════════════════════════════════════════════
# Red-Team Case 9: Conflicting signals → conservative result wins
# ══════════════════════════════════════════════════════════════════════


def test_ci_failure_on_non_react_dep_would_hold():
    """CI failure on any dependency update should result in hold."""
    policy = _make_policy(
        evidence_refs=(_make_evidence("candidate_rule"),),
        owner=_make_owner(),
        rollback_plan=_make_rollback(),
    )
    case = PolicyShadowCase(
        case_id="RT-009",
        description="Dependabot PR with CI failure on non-react dependency",
        actor_type="dependabot",
        has_ci_failure=True,
        is_react_update=False,
        expected_verdict=ShadowVerdict.WOULD_HOLD,
    )
    result = evaluator.evaluate(policy, case)
    assert result.verdict == ShadowVerdict.WOULD_HOLD


# ══════════════════════════════════════════════════════════════════════
# Red-Team Case 10: Unknown actor → would_escalate
# ══════════════════════════════════════════════════════════════════════


def test_unknown_actor_would_escalate():
    policy = _make_policy()
    case = PolicyShadowCase(
        case_id="RT-010",
        description="Unknown actor_type should trigger conservative escalation",
        actor_type="unknown",
        expected_verdict=ShadowVerdict.WOULD_ESCALATE,
    )
    result = evaluator.evaluate(policy, case)
    assert result.verdict == ShadowVerdict.WOULD_ESCALATE
    assert result.confidence < 0.5


# ══════════════════════════════════════════════════════════════════════
# Case 11: AI agent actor → would_escalate
# ══════════════════════════════════════════════════════════════════════


def test_ai_agent_would_escalate():
    policy = _make_policy()
    case = PolicyShadowCase(
        case_id="RT-011",
        description="AI agent PR requires human review (doctrine §4.3)",
        actor_type="ai_agent",
        expected_verdict=ShadowVerdict.WOULD_ESCALATE,
    )
    result = evaluator.evaluate(policy, case)
    assert result.verdict == ShadowVerdict.WOULD_ESCALATE


# ══════════════════════════════════════════════════════════════════════
# Invariants
# ══════════════════════════════════════════════════════════════════════


def test_shadow_evaluator_never_mutates_policy():
    policy = _make_policy(state=PolicyState.DRAFT)
    original = policy.state
    case = PolicyShadowCase(
        case_id="INV-001",
        description="Mutation check",
        actor_type="dependabot",
    )
    evaluator.evaluate(policy, case)
    assert policy.state == original
    assert policy.state == PolicyState.DRAFT


def test_shadow_evaluator_never_changes_policy_state():
    for state in PolicyState:
        if state in (
            PolicyState.ACTIVE_SHADOW,
            PolicyState.ACTIVE_ENFORCED,
            PolicyState.ROLLED_BACK,
            PolicyState.DEPRECATED,
        ):
            continue  # these states need metadata not relevant to this test
        policy = _make_policy(state=state)
        case = PolicyShadowCase(case_id=f"INV-{state.value}", description="State check", actor_type="human")
        evaluator.evaluate(policy, case)
        assert policy.state == state


def test_shadow_result_is_always_advisory():
    policy = _make_policy()
    case = PolicyShadowCase(case_id="INV-ADV", description="Advisory check", actor_type="dependabot")
    result = evaluator.evaluate(policy, case)
    assert result.is_advisory
    assert not isinstance(result, bool)  # not a simple pass/fail


def test_activation_readiness_is_not_auto_activation():
    """READY_FOR_ACTIVATION from the evidence gate does NOT auto-activate."""
    policy = _make_policy(
        state=PolicyState.DRAFT,
        evidence_refs=(
            _make_evidence("candidate_rule"),
            _make_evidence("lesson"),
            _make_evidence("review"),
        ),
        owner=_make_owner(),
        rollback_plan=_make_rollback(),
    )
    gate_result = evaluator._evidence_gate.assess(policy)
    assert gate_result.level == ReadinessLevel.READY_FOR_HUMAN_ACTIVATION_REVIEW
    # But the policy state must remain DRAFT
    assert policy.state == PolicyState.DRAFT
    # The evaluator does not transition the policy
    assert evaluator.activation_readiness_check(policy) is True


def test_evaluate_batch_returns_all_results():
    policy = _make_policy()
    cases = [
        PolicyShadowCase(case_id="B-001", description="Batch 1", actor_type="human"),
        PolicyShadowCase(case_id="B-002", description="Batch 2", actor_type="dependabot"),
        PolicyShadowCase(case_id="B-003", description="Batch 3", actor_type="unknown"),
    ]
    results = evaluator.evaluate_batch(policy, cases)
    assert len(results) == 3
    for r in results:
        assert r.is_advisory


def test_would_block_and_would_require_review():
    reject = PolicyShadowResult(
        case_id="T",
        policy_id="P",
        verdict=ShadowVerdict.WOULD_REJECT,
    )
    assert reject.would_block
    assert not reject.would_require_review

    escalate = PolicyShadowResult(
        case_id="T",
        policy_id="P",
        verdict=ShadowVerdict.WOULD_ESCALATE,
    )
    assert not escalate.would_block
    assert escalate.would_require_review

    hold = PolicyShadowResult(
        case_id="T",
        policy_id="P",
        verdict=ShadowVerdict.WOULD_HOLD,
    )
    assert not hold.would_block
    assert hold.would_require_review

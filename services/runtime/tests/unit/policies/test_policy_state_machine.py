"""Unit tests for Policy Platform state machine (Phase 5.2 prototype).

Tests validate:
  - All valid lifecycle transitions
  - All invalid/forbidden transitions
  - Activation boundary guards (missing evidence, owner, rollback_plan)
  - Terminal state behavior
  - Rollback and deprecation semantics
  - Scope and risk validation
  - Pure model behavior (no side effects, no ORM, no RiskEngine imports)
"""

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
    OwnerType,
    EvidenceFreshness,
)
from domains.policies.state_machine import (
    PolicyStateMachine,
    TransitionResult,
)


# ── Helpers ──────────────────────────────────────────────────────────


def _make_policy(
    policy_id: str = "POL-001",
    title: str = "Test Policy",
    scope: PolicyScope = PolicyScope.CORE,
    state: PolicyState = PolicyState.DRAFT,
    risk: PolicyRisk = PolicyRisk.LOW,
    evidence_refs: tuple[PolicyEvidenceRef, ...] = (),
    owner: PolicyOwner | None = None,
    rollback_plan: PolicyRollbackPlan | None = None,
    version: int = 1,
    **kwargs,
) -> PolicyRecord:
    return PolicyRecord(
        policy_id=policy_id,
        title=title,
        scope=scope,
        state=state,
        risk=risk,
        evidence_refs=evidence_refs,
        owner=owner,
        rollback_plan=rollback_plan,
        version=version,
        created_at=datetime.now(timezone.utc),
        **kwargs,
    )


def _make_evidence() -> PolicyEvidenceRef:
    return PolicyEvidenceRef(
        ref_type="candidate_rule",
        ref_id="CR-001",
        freshness=EvidenceFreshness.CURRENT,
    )


def _make_owner() -> PolicyOwner:
    return PolicyOwner(owner_id="alice", owner_type=OwnerType.INDIVIDUAL)


def _make_rollback_plan() -> PolicyRollbackPlan:
    return PolicyRollbackPlan(
        trigger="false_positive_rate > 5%",
        authorized_by="alice",
        method="state_transition",
        blast_radius="CI gate repo-governance-pr",
        target_recovery_time="seconds",
    )


# ── Valid Lifecycle Path ─────────────────────────────────────────────


def test_full_valid_lifecycle_path():
    """A Policy should traverse the complete valid lifecycle:
    draft → proposed → approved → active_shadow → active_enforced → deprecated.
    """
    machine = PolicyStateMachine()
    evidence = _make_evidence()
    owner = _make_owner()
    rollback = _make_rollback_plan()

    # draft → proposed
    policy = _make_policy(state=PolicyState.DRAFT)
    result = machine.transition(policy, PolicyState.PROPOSED)
    assert result.allowed
    policy = result.new_policy
    assert policy.state == PolicyState.PROPOSED

    # proposed → approved
    result = machine.transition(policy, PolicyState.APPROVED)
    assert result.allowed
    policy = result.new_policy
    assert policy.state == PolicyState.APPROVED

    # approved → active_shadow (requires evidence, owner, rollback_plan)
    policy_with_meta = _make_policy(
        policy_id=policy.policy_id,
        state=PolicyState.APPROVED,
        evidence_refs=(evidence,),
        owner=owner,
        rollback_plan=rollback,
        version=policy.version,
    )
    result = machine.transition(policy_with_meta, PolicyState.ACTIVE_SHADOW)
    assert result.allowed
    policy = result.new_policy
    assert policy.state == PolicyState.ACTIVE_SHADOW

    # active_shadow → active_enforced
    result = machine.transition(policy, PolicyState.ACTIVE_ENFORCED)
    assert result.allowed
    policy = result.new_policy
    assert policy.state == PolicyState.ACTIVE_ENFORCED

    # active_enforced → deprecated
    result = machine.transition(policy, PolicyState.DEPRECATED, deprecation_reason="No longer needed")
    assert result.allowed
    policy = result.new_policy
    assert policy.state == PolicyState.DEPRECATED

    # deprecated is terminal
    assert PolicyStateMachine.is_terminal(policy.state)


def test_full_valid_lifecycle_with_rejection():
    """draft → proposed → rejected is a valid path."""
    machine = PolicyStateMachine()
    policy = _make_policy(state=PolicyState.DRAFT)
    result = machine.transition(policy, PolicyState.PROPOSED)
    assert result.allowed
    result = machine.transition(result.new_policy, PolicyState.REJECTED)
    assert result.allowed
    assert result.new_policy.state == PolicyState.REJECTED
    assert PolicyStateMachine.is_terminal(result.new_policy.state)


# ── Invalid Direct Activation ────────────────────────────────────────


def test_draft_cannot_jump_to_active_shadow():
    """Draft → active_shadow must be rejected."""
    machine = PolicyStateMachine()
    policy = _make_policy(state=PolicyState.DRAFT)
    result = machine.transition(policy, PolicyState.ACTIVE_SHADOW)
    assert not result.allowed
    assert any("Invalid transition" in r for r in result.reasons)


def test_draft_cannot_jump_to_active_enforced():
    """Draft → active_enforced must be rejected."""
    machine = PolicyStateMachine()
    policy = _make_policy(state=PolicyState.DRAFT)
    result = machine.transition(policy, PolicyState.ACTIVE_ENFORCED)
    assert not result.allowed
    assert any("Invalid" in r for r in result.reasons)


def test_proposed_cannot_jump_to_active_enforced():
    """Proposed → active_enforced must be rejected."""
    machine = PolicyStateMachine()
    policy = _make_policy(state=PolicyState.PROPOSED)
    result = machine.transition(policy, PolicyState.ACTIVE_ENFORCED)
    assert not result.allowed


def test_approved_cannot_jump_to_active_enforced():
    """Approved → active_enforced without passing through active_shadow is rejected."""
    machine = PolicyStateMachine()
    policy = _make_policy(
        state=PolicyState.APPROVED,
        evidence_refs=(_make_evidence(),),
        owner=_make_owner(),
        rollback_plan=_make_rollback_plan(),
    )
    result = machine.transition(policy, PolicyState.ACTIVE_ENFORCED)
    assert not result.allowed


# ── Terminal States ──────────────────────────────────────────────────


@pytest.mark.parametrize(
    "terminal_state,extra_kwargs",
    [
        (PolicyState.DEPRECATED, {"deprecation_reason": "Test deprecation"}),
        (PolicyState.ROLLED_BACK, {"rollback_reason": "Test rollback"}),
        (PolicyState.REJECTED, {}),
    ],
)
def test_terminal_states_have_no_outgoing_transitions(terminal_state, extra_kwargs):
    """Terminal states should reject any transition attempt."""
    machine = PolicyStateMachine()
    for target in PolicyState:
        if target == terminal_state:
            continue
        policy = _make_policy(state=terminal_state, **extra_kwargs)
        result = machine.transition(policy, target)
        assert not result.allowed, f"{terminal_state.value} → {target.value} should be rejected"


def test_rejected_is_terminal_cannot_resubmit():
    """A rejected policy cannot be resubmitted. Must create new draft."""
    machine = PolicyStateMachine()
    policy = _make_policy(state=PolicyState.REJECTED)
    result = machine.transition(policy, PolicyState.PROPOSED)
    assert not result.allowed


# ── Missing Evidence Rejected ────────────────────────────────────────


def test_activation_without_evidence_rejected():
    """active_shadow requires evidence_refs."""
    machine = PolicyStateMachine()
    policy = _make_policy(
        state=PolicyState.APPROVED,
        owner=_make_owner(),
        rollback_plan=_make_rollback_plan(),
        # no evidence_refs
    )
    result = machine.transition(policy, PolicyState.ACTIVE_SHADOW)
    assert not result.allowed
    assert any("evidence" in r.lower() for r in result.reasons)


# ── Missing Owner Rejected ───────────────────────────────────────────


def test_activation_without_owner_rejected():
    """active_shadow requires owner."""
    machine = PolicyStateMachine()
    policy = _make_policy(
        state=PolicyState.APPROVED,
        evidence_refs=(_make_evidence(),),
        rollback_plan=_make_rollback_plan(),
        # no owner
    )
    result = machine.transition(policy, PolicyState.ACTIVE_SHADOW)
    assert not result.allowed
    assert any("owner" in r.lower() for r in result.reasons)


# ── Missing Rollback Plan Rejected ───────────────────────────────────


def test_activation_without_rollback_plan_rejected():
    """active_shadow requires rollback_plan."""
    machine = PolicyStateMachine()
    policy = _make_policy(
        state=PolicyState.APPROVED,
        evidence_refs=(_make_evidence(),),
        owner=_make_owner(),
        # no rollback_plan
    )
    result = machine.transition(policy, PolicyState.ACTIVE_SHADOW)
    assert not result.allowed
    assert any("rollback" in r.lower() for r in result.reasons)


# ── Rollback from Active Enforced ────────────────────────────────────


def test_rollback_from_active_enforced():
    """active_enforced → rolled_back with reason should succeed."""
    machine = PolicyStateMachine()
    policy = _make_policy(
        state=PolicyState.ACTIVE_ENFORCED,
        evidence_refs=(_make_evidence(),),
        owner=_make_owner(),
        rollback_plan=_make_rollback_plan(),
    )
    result = machine.transition(policy, PolicyState.ROLLED_BACK, rollback_reason="False positive rate exceeded 5%")
    assert result.allowed
    assert result.new_policy.state == PolicyState.ROLLED_BACK
    assert result.new_policy.rollback_reason == "False positive rate exceeded 5%"


def test_rollback_without_reason_rejected():
    """active_enforced → rolled_back without reason must be rejected."""
    machine = PolicyStateMachine()
    policy = _make_policy(
        state=PolicyState.ACTIVE_ENFORCED,
        evidence_refs=(_make_evidence(),),
        owner=_make_owner(),
        rollback_plan=_make_rollback_plan(),
    )
    result = machine.transition(policy, PolicyState.ROLLED_BACK)
    assert not result.allowed
    assert any("rollback_reason" in r.lower() for r in result.reasons)


# ── Deprecate from Active Shadow ─────────────────────────────────────


def test_deprecate_from_active_shadow():
    """active_shadow → deprecated with reason should succeed."""
    machine = PolicyStateMachine()
    policy = _make_policy(
        state=PolicyState.ACTIVE_SHADOW,
        evidence_refs=(_make_evidence(),),
        owner=_make_owner(),
        rollback_plan=_make_rollback_plan(),
    )
    result = machine.transition(policy, PolicyState.DEPRECATED, deprecation_reason="Replaced by POL-002")
    assert result.allowed
    assert result.new_policy.state == PolicyState.DEPRECATED
    assert result.new_policy.deprecation_reason == "Replaced by POL-002"


def test_deprecate_without_reason_rejected():
    """active_enforced → deprecated without reason must be rejected."""
    machine = PolicyStateMachine()
    policy = _make_policy(
        state=PolicyState.ACTIVE_ENFORCED,
        evidence_refs=(_make_evidence(),),
        owner=_make_owner(),
        rollback_plan=_make_rollback_plan(),
    )
    result = machine.transition(policy, PolicyState.DEPRECATED)
    assert not result.allowed
    assert any("deprecation_reason" in r.lower() for r in result.reasons)


# ── Scope and Risk Validation ────────────────────────────────────────


def test_policy_record_requires_policy_id():
    with pytest.raises(ValueError, match="policy_id"):
        PolicyRecord(
            policy_id="",
            title="Test",
            scope=PolicyScope.CORE,
            state=PolicyState.DRAFT,
            risk=PolicyRisk.LOW,
        )


def test_policy_record_requires_title():
    with pytest.raises(ValueError, match="title"):
        PolicyRecord(
            policy_id="POL-001",
            title="",
            scope=PolicyScope.CORE,
            state=PolicyState.DRAFT,
            risk=PolicyRisk.LOW,
        )


def test_evidence_ref_requires_ref_type():
    with pytest.raises(ValueError, match="ref_type"):
        PolicyEvidenceRef(ref_type="", ref_id="CR-001")


def test_evidence_ref_requires_ref_id():
    with pytest.raises(ValueError, match="ref_id"):
        PolicyEvidenceRef(ref_type="candidate_rule", ref_id="")


def test_rollback_plan_requires_all_fields():
    with pytest.raises(ValueError, match="all fields"):
        PolicyRollbackPlan(
            trigger="",
            authorized_by="alice",
            method="state_transition",
            blast_radius="CI",
            target_recovery_time="seconds",
        )


def test_owner_requires_owner_id():
    with pytest.raises(ValueError, match="owner_id"):
        PolicyOwner(owner_id="")


def test_all_scopes_accepted():
    """All defined PolicyScope values should be usable."""
    for scope in PolicyScope:
        policy = _make_policy(scope=scope)
        assert policy.scope == scope


def test_all_risk_levels_accepted():
    """All defined PolicyRisk values should be usable."""
    for risk in PolicyRisk:
        policy = _make_policy(risk=risk)
        assert policy.risk == risk


# ── No Side Effects / Pure Model Behavior ────────────────────────────


def test_policy_record_is_frozen():
    """PolicyRecord should be immutable (frozen dataclass)."""
    policy = _make_policy()
    with pytest.raises(Exception):
        policy.state = PolicyState.ACTIVE_SHADOW  # type: ignore[misc]


def test_transition_result_is_frozen():
    """TransitionResult should be immutable."""
    result = TransitionResult(allowed=True, reasons=())
    with pytest.raises(Exception):
        result.allowed = False  # type: ignore[misc]


def test_state_machine_has_no_imports_from_risk_engine():
    """The state machine must not import from RiskEngine, governance, pack, execution, or ORM modules."""
    import inspect
    from domains.policies import state_machine as sm

    source_lines = inspect.getsource(sm).split("\n")
    forbidden = ["risk_engine", "governance_engine.", "packs.", "execution.", "sqlalchemy"]
    for word in forbidden:
        for line in source_lines:
            stripped = line.strip()
            if stripped.startswith('"""') or stripped.startswith("#"):
                continue
            if word in line.lower():
                raise AssertionError(f"State machine source contains forbidden import: {word} in line: {stripped[:80]}")


def test_models_have_no_imports_from_risk_engine():
    """The models must not import from RiskEngine, governance, pack, execution, or ORM modules."""
    import inspect
    from domains.policies import models as m

    source_lines = inspect.getsource(m).split("\n")
    forbidden = ["risk_engine", "governance_engine.", "packs.", "execution.", "sqlalchemy"]
    for word in forbidden:
        for line in source_lines:
            # Skip docstring lines and comments
            stripped = line.strip()
            if stripped.startswith('"""') or stripped.startswith("#"):
                continue
            if word in line.lower():
                raise AssertionError(f"Models source contains forbidden import: {word} in line: {stripped[:80]}")


# ── Versioning ───────────────────────────────────────────────────────


def test_transition_increments_version():
    """Each transition should increment the version number."""
    machine = PolicyStateMachine()
    policy = _make_policy(state=PolicyState.DRAFT, version=1)
    result = machine.transition(policy, PolicyState.PROPOSED)
    assert result.new_policy.version == 2

    result2 = machine.transition(result.new_policy, PolicyState.APPROVED)
    assert result2.new_policy.version == 3


# ══════════════════════════════════════════════════════════════════════
# Phase 5.2-P — Direct Construction Invariant Tests
# ══════════════════════════════════════════════════════════════════════


def test_direct_construction_active_shadow_without_evidence_fails():
    """Cannot directly construct ACTIVE_SHADOW without evidence_refs."""
    with pytest.raises(ValueError, match="PolicyEvidenceRef"):
        _make_policy(
            state=PolicyState.ACTIVE_SHADOW,
            owner=_make_owner(),
            rollback_plan=_make_rollback_plan(),
            # no evidence_refs
        )


def test_direct_construction_active_shadow_without_owner_fails():
    """Cannot directly construct ACTIVE_SHADOW without owner."""
    with pytest.raises(ValueError, match="PolicyOwner"):
        _make_policy(
            state=PolicyState.ACTIVE_SHADOW,
            evidence_refs=(_make_evidence(),),
            rollback_plan=_make_rollback_plan(),
            # no owner
        )


def test_direct_construction_active_shadow_without_rollback_fails():
    """Cannot directly construct ACTIVE_SHADOW without rollback_plan."""
    with pytest.raises(ValueError, match="PolicyRollbackPlan"):
        _make_policy(
            state=PolicyState.ACTIVE_SHADOW,
            evidence_refs=(_make_evidence(),),
            owner=_make_owner(),
            # no rollback_plan
        )


def test_direct_construction_active_enforced_without_evidence_fails():
    """Cannot directly construct ACTIVE_ENFORCED without evidence_refs."""
    with pytest.raises(ValueError, match="PolicyEvidenceRef"):
        _make_policy(
            state=PolicyState.ACTIVE_ENFORCED,
            owner=_make_owner(),
            rollback_plan=_make_rollback_plan(),
        )


def test_direct_construction_active_enforced_without_owner_fails():
    """Cannot directly construct ACTIVE_ENFORCED without owner."""
    with pytest.raises(ValueError, match="PolicyOwner"):
        _make_policy(
            state=PolicyState.ACTIVE_ENFORCED,
            evidence_refs=(_make_evidence(),),
            rollback_plan=_make_rollback_plan(),
        )


def test_direct_construction_active_enforced_without_rollback_fails():
    """Cannot directly construct ACTIVE_ENFORCED without rollback_plan."""
    with pytest.raises(ValueError, match="PolicyRollbackPlan"):
        _make_policy(
            state=PolicyState.ACTIVE_ENFORCED,
            evidence_refs=(_make_evidence(),),
            owner=_make_owner(),
        )


def test_direct_construction_rolled_back_without_reason_fails():
    """Cannot directly construct ROLLED_BACK without rollback_reason."""
    with pytest.raises(ValueError, match="rollback_reason"):
        _make_policy(
            state=PolicyState.ROLLED_BACK,
            evidence_refs=(_make_evidence(),),
            owner=_make_owner(),
            rollback_plan=_make_rollback_plan(),
            # no rollback_reason
        )


def test_direct_construction_deprecated_without_reason_fails():
    """Cannot directly construct DEPRECATED without deprecation_reason."""
    with pytest.raises(ValueError, match="deprecation_reason"):
        _make_policy(
            state=PolicyState.DEPRECATED,
            evidence_refs=(_make_evidence(),),
            owner=_make_owner(),
            rollback_plan=_make_rollback_plan(),
            # no deprecation_reason
        )


def test_direct_construction_valid_active_shadow_succeeds():
    """Direct construction of ACTIVE_SHADOW with all required metadata should succeed."""
    policy = _make_policy(
        state=PolicyState.ACTIVE_SHADOW,
        evidence_refs=(_make_evidence(),),
        owner=_make_owner(),
        rollback_plan=_make_rollback_plan(),
    )
    assert policy.state == PolicyState.ACTIVE_SHADOW


def test_direct_construction_valid_rolled_back_succeeds():
    """Direct construction of ROLLED_BACK with reason should succeed."""
    policy = _make_policy(
        state=PolicyState.ROLLED_BACK,
        evidence_refs=(_make_evidence(),),
        owner=_make_owner(),
        rollback_plan=_make_rollback_plan(),
        rollback_reason="Emergency rollback",
    )
    assert policy.state == PolicyState.ROLLED_BACK
    assert policy.rollback_reason == "Emergency rollback"


def test_direct_construction_valid_deprecated_succeeds():
    """Direct construction of DEPRECATED with reason should succeed."""
    policy = _make_policy(
        state=PolicyState.DEPRECATED,
        evidence_refs=(_make_evidence(),),
        owner=_make_owner(),
        rollback_plan=_make_rollback_plan(),
        deprecation_reason="No longer needed",
    )
    assert policy.state == PolicyState.DEPRECATED
    assert policy.deprecation_reason == "No longer needed"


def test_direct_construction_draft_without_metadata_succeeds():
    """Draft state without evidence/owner/rollback should still succeed
    (these are only required for activation states)."""
    policy = _make_policy(state=PolicyState.DRAFT)
    assert policy.state == PolicyState.DRAFT


def test_with_state_unchecked_still_works_for_state_machine():
    """Verify _with_state_unchecked still creates new PolicyRecord.
    The state machine uses this internally after validating transitions."""
    machine = PolicyStateMachine()
    policy = _make_policy(state=PolicyState.DRAFT)
    result = machine.transition(policy, PolicyState.PROPOSED)
    assert result.allowed
    assert result.new_policy.state == PolicyState.PROPOSED
    assert result.new_policy.version == 2


def test_transition_preserves_predecessor():
    """New policy should reference its predecessor via predecessor_policy_id."""
    machine = PolicyStateMachine()
    policy = _make_policy(state=PolicyState.DRAFT, policy_id="POL-001")
    result = machine.transition(policy, PolicyState.PROPOSED)
    assert result.new_policy.predecessor_policy_id == "POL-001"


# ── allowed_transitions_from ─────────────────────────────────────────


def test_allowed_transitions_from_draft():
    """Draft should allow proposed and rejected."""
    allowed = PolicyStateMachine.allowed_transitions_from(PolicyState.DRAFT)
    assert allowed == {PolicyState.PROPOSED, PolicyState.REJECTED}


def test_allowed_transitions_from_active_enforced():
    """Active enforced should allow deprecated and rolled_back."""
    allowed = PolicyStateMachine.allowed_transitions_from(PolicyState.ACTIVE_ENFORCED)
    assert allowed == {PolicyState.DEPRECATED, PolicyState.ROLLED_BACK}


def test_allowed_transitions_from_terminal_are_empty():
    """Terminal states should have no allowed transitions."""
    for state in (PolicyState.DEPRECATED, PolicyState.ROLLED_BACK, PolicyState.REJECTED):
        assert PolicyStateMachine.allowed_transitions_from(state) == set()


# ── Same-state transition ────────────────────────────────────────────


def test_same_state_transition_rejected():
    """Transitioning to the same state should be rejected as no-op."""
    machine = PolicyStateMachine()
    policy = _make_policy(state=PolicyState.DRAFT)
    result = machine.transition(policy, PolicyState.DRAFT)
    assert not result.allowed
    assert any("already in state" in r for r in result.reasons)


# ── can_transition ───────────────────────────────────────────────────


def test_can_transition_returns_true_for_valid():
    machine = PolicyStateMachine()
    policy = _make_policy(state=PolicyState.DRAFT)
    assert machine.can_transition(policy, PolicyState.PROPOSED) is True


def test_can_transition_returns_false_for_invalid():
    machine = PolicyStateMachine()
    policy = _make_policy(state=PolicyState.DRAFT)
    assert machine.can_transition(policy, PolicyState.ACTIVE_ENFORCED) is False

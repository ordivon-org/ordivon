"""CandidateRulePolicyBridge tests — accepted_candidate → PolicyRecord(draft) path.

Phase 5.3 boundary alignment: the bridge now creates PolicyRecord(draft)
instead of the retired PolicyProposal dataclass.
"""

import pytest
from unittest.mock import MagicMock

from domains.candidate_rules.policy_proposal import (
    CandidateRulePolicyBridge,
    DuplicateProposalError,
    ProposalNotAllowedError,
)
from domains.candidate_rules.repository import CandidateRuleRepository
from domains.policies.models import PolicyState, EvidenceFreshness


def _mock_row(
    status="accepted_candidate",
    source_refs_json='["review:r1","lesson:L1","reviewer:alice"]',
    summary="Test rule",
):
    row = MagicMock()
    row.status = status
    row.source_refs_json = source_refs_json
    row.summary = summary
    return row


def _make_bridge(row=None):
    db = MagicMock()
    repo = CandidateRuleRepository(db)
    if row:
        repo.get = MagicMock(return_value=row)
    return CandidateRulePolicyBridge(repo), repo


# ═══════════════════════════════════════════════════════════════════════
# Test 1: accepted_candidate → PolicyRecord(draft)
# ═══════════════════════════════════════════════════════════════════════


def test_accepted_candidate_creates_draft_policy():
    bridge, _ = _make_bridge(_mock_row("accepted_candidate"))
    policy = bridge.create_policy_draft("crule_001", created_by="admin", rationale="Clear pattern")
    assert policy.state == PolicyState.DRAFT
    assert policy.title == "Test rule"
    assert len(policy.evidence_refs) > 0
    assert any("candidate_rule:crule_001" in r.ref_id for r in policy.evidence_refs)


def test_accepted_candidate_policy_is_not_active():
    bridge, _ = _make_bridge(_mock_row("accepted_candidate"))
    policy = bridge.create_policy_draft("crule_002", created_by="admin", rationale="test")
    assert policy.state == PolicyState.DRAFT
    assert policy.state != PolicyState.ACTIVE_SHADOW
    assert policy.state != PolicyState.ACTIVE_ENFORCED


# ═══════════════════════════════════════════════════════════════════════
# Test 2: draft candidate cannot create policy
# ═══════════════════════════════════════════════════════════════════════


def test_draft_cannot_create_policy():
    bridge, _ = _make_bridge(_mock_row("draft"))
    with pytest.raises(ProposalNotAllowedError, match="draft"):
        bridge.create_policy_draft("crule_003", created_by="admin", rationale="test")


# ═══════════════════════════════════════════════════════════════════════
# Test 3: under_review cannot create policy
# ═══════════════════════════════════════════════════════════════════════


def test_under_review_cannot_create_policy():
    bridge, _ = _make_bridge(_mock_row("under_review"))
    with pytest.raises(ProposalNotAllowedError, match="under_review"):
        bridge.create_policy_draft("crule_004", created_by="admin", rationale="test")


# ═══════════════════════════════════════════════════════════════════════
# Test 4: rejected cannot create policy
# ═══════════════════════════════════════════════════════════════════════


def test_rejected_cannot_create_policy():
    bridge, _ = _make_bridge(_mock_row("rejected"))
    with pytest.raises(ProposalNotAllowedError, match="rejected"):
        bridge.create_policy_draft("crule_005", created_by="admin", rationale="test")


# ═══════════════════════════════════════════════════════════════════════
# Test 5: duplicate policy draft rejected
# ═══════════════════════════════════════════════════════════════════════


def test_duplicate_draft_rejected():
    bridge, _ = _make_bridge(_mock_row("accepted_candidate"))
    bridge.create_policy_draft("crule_006", created_by="admin", rationale="First")
    with pytest.raises(DuplicateProposalError, match="crule_006"):
        bridge.create_policy_draft("crule_006", created_by="admin", rationale="Second")


# ═══════════════════════════════════════════════════════════════════════
# Test 6: evidence refs carry over from CandidateRule lineage
# ═══════════════════════════════════════════════════════════════════════


def test_evidence_refs_preserved():
    bridge, _ = _make_bridge(
        _mock_row("accepted_candidate", source_refs_json='["review:r1","lesson:L1","reviewer:alice"]')
    )
    policy = bridge.create_policy_draft("crule_007", created_by="admin", rationale="test")
    ref_ids = {r.ref_id for r in policy.evidence_refs}
    assert "review:r1" in ref_ids
    assert "lesson:L1" in ref_ids
    assert "reviewer:alice" in ref_ids
    assert "candidate_rule:crule_007" in ref_ids


def test_evidence_refs_have_correct_types():
    bridge, _ = _make_bridge(_mock_row("accepted_candidate", source_refs_json='["review:r1","lesson:L1"]'))
    policy = bridge.create_policy_draft("crule_008", created_by="admin", rationale="test")
    ref_types = {r.ref_type for r in policy.evidence_refs}
    assert "review" in ref_types
    assert "lesson" in ref_types
    assert "candidate_rule" in ref_types


def test_evidence_refs_are_fresh():
    bridge, _ = _make_bridge(_mock_row("accepted_candidate"))
    policy = bridge.create_policy_draft("crule_009", created_by="admin", rationale="test")
    for ref in policy.evidence_refs:
        assert ref.freshness == EvidenceFreshness.CURRENT


# ═══════════════════════════════════════════════════════════════════════
# Test 7: no active policy can emerge from bridge
# ═══════════════════════════════════════════════════════════════════════


def test_bridge_never_creates_active_policy():
    bridge, _ = _make_bridge(_mock_row("accepted_candidate"))
    policy = bridge.create_policy_draft("crule_010", created_by="admin", rationale="test")
    assert policy.state == PolicyState.DRAFT
    # Confirm the bridge physically cannot set state to active
    assert policy.state not in (PolicyState.ACTIVE_SHADOW, PolicyState.ACTIVE_ENFORCED)


def test_draft_policy_has_no_owner():
    bridge, _ = _make_bridge(_mock_row("accepted_candidate"))
    policy = bridge.create_policy_draft("crule_011", created_by="admin", rationale="test")
    assert policy.owner is None  # owner only required at activation, not draft


def test_draft_policy_has_no_rollback_plan():
    bridge, _ = _make_bridge(_mock_row("accepted_candidate"))
    policy = bridge.create_policy_draft("crule_012", created_by="admin", rationale="test")
    assert policy.rollback_plan is None  # only required at activation


# ═══════════════════════════════════════════════════════════════════════
# Test 8: bridge does not modify Pack policy
# ═══════════════════════════════════════════════════════════════════════


def test_bridge_does_not_modify_pack_policy():
    bridge, _ = _make_bridge(_mock_row("accepted_candidate"))
    policy = bridge.create_policy_draft("crule_013", created_by="admin", rationale="test")
    assert policy.state == PolicyState.DRAFT


# ═══════════════════════════════════════════════════════════════════════
# Test 9: no RiskEngine imports
# ═══════════════════════════════════════════════════════════════════════


def test_bridge_does_not_import_risk_engine():
    import inspect
    from domains.candidate_rules import policy_proposal as mod

    src = inspect.getsource(mod)
    import_lines = [l for l in src.splitlines() if l.strip().startswith(("from ", "import "))]
    assert "RiskEngine" not in "\n".join(import_lines)
    assert "governance.risk_engine" not in "\n".join(import_lines)


# ═══════════════════════════════════════════════════════════════════════
# Test 10: no ExecutionRequest/Receipt
# ═══════════════════════════════════════════════════════════════════════


def test_bridge_no_execution_side_effects():
    import inspect
    from domains.candidate_rules import policy_proposal as mod

    src = inspect.getsource(mod)
    import_lines = [l for l in src.splitlines() if l.strip().startswith(("from ", "import "))]
    forbidden = ["ExecutionRequest", "ExecutionReceipt"]
    for word in forbidden:
        assert word not in "\n".join(import_lines), f"Forbidden import: {word}"


# ═══════════════════════════════════════════════════════════════════════
# Test 11: no broker/order/trade/shell/MCP/IDE
# ═══════════════════════════════════════════════════════════════════════


def test_bridge_no_broker_imports():
    import inspect
    from domains.candidate_rules import policy_proposal as mod

    src = inspect.getsource(mod)
    import_lines = [l for l in src.splitlines() if l.strip().startswith(("from ", "import "))]
    forbidden = ["broker", "place_order", "execute_trade", "shell", "MCP"]
    for word in forbidden:
        assert word not in "\n".join(import_lines), f"Forbidden import: {word}"


# ═══════════════════════════════════════════════════════════════════════
# Test 12: list_drafts and get_draft
# ═══════════════════════════════════════════════════════════════════════


def test_list_drafts_returns_all():
    bridge, _ = _make_bridge(_mock_row("accepted_candidate"))
    bridge.create_policy_draft("crule_a", created_by="admin", rationale="A")
    bridge.create_policy_draft("crule_b", created_by="admin", rationale="B")
    drafts = bridge.list_drafts()
    assert len(drafts) == 2


def test_get_draft_returns_correct():
    bridge, _ = _make_bridge(_mock_row("accepted_candidate"))
    bridge.create_policy_draft("crule_c", created_by="admin", rationale="test")
    draft = bridge.get_draft("crule_c")
    assert draft is not None
    assert draft.state == PolicyState.DRAFT


def test_get_draft_returns_none_for_unknown():
    bridge, _ = _make_bridge(_mock_row("accepted_candidate"))
    assert bridge.get_draft("nonexistent") is None

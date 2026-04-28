"""PolicyProposal Service tests — accepted_candidate → PolicyProposal(draft) path."""

import pytest
from unittest.mock import MagicMock

from domains.candidate_rules.policy_proposal import (
    PolicyProposal,
    PolicyProposalService,
    DuplicateProposalError,
    ProposalNotAllowedError,
)
from domains.candidate_rules.repository import CandidateRuleRepository


def _mock_row(
    status="accepted_candidate", source_refs_json='["review:r1","lesson:L1","reviewer:alice"]', summary="Test rule"
):
    row = MagicMock()
    row.status = status
    row.source_refs_json = source_refs_json
    row.summary = summary
    return row


def _make_service(row=None):
    db = MagicMock()
    repo = CandidateRuleRepository(db)
    if row:
        repo.get = MagicMock(return_value=row)
    return PolicyProposalService(repo), repo


# ═══════════════════════════════════════════════════════════════════════
# Test 1: accepted_candidate → PolicyProposal(draft)
# ═══════════════════════════════════════════════════════════════════════


def test_accepted_candidate_creates_proposal():
    svc, _ = _make_service(_mock_row("accepted_candidate"))
    proposal = svc.propose_from_accepted("crule_001", created_by="admin", rationale="Clear pattern")
    assert proposal.status == "draft"
    assert proposal.candidate_rule_id == "crule_001"
    assert proposal.created_by == "admin"
    assert proposal.rationale == "Clear pattern"
    assert "candidate_rule:crule_001" in proposal.source_refs


# ═══════════════════════════════════════════════════════════════════════
# Test 2: draft cannot create proposal
# ═══════════════════════════════════════════════════════════════════════


def test_draft_cannot_create_proposal():
    svc, _ = _make_service(_mock_row("draft"))
    with pytest.raises(ProposalNotAllowedError, match="draft"):
        svc.propose_from_accepted("crule_002", created_by="admin", rationale="test")


# ═══════════════════════════════════════════════════════════════════════
# Test 3: under_review cannot create proposal
# ═══════════════════════════════════════════════════════════════════════


def test_under_review_cannot_create_proposal():
    svc, _ = _make_service(_mock_row("under_review"))
    with pytest.raises(ProposalNotAllowedError, match="under_review"):
        svc.propose_from_accepted("crule_003", created_by="admin", rationale="test")


# ═══════════════════════════════════════════════════════════════════════
# Test 4: rejected cannot create proposal
# ═══════════════════════════════════════════════════════════════════════


def test_rejected_cannot_create_proposal():
    svc, _ = _make_service(_mock_row("rejected"))
    with pytest.raises(ProposalNotAllowedError, match="rejected"):
        svc.propose_from_accepted("crule_004", created_by="admin", rationale="test")


# ═══════════════════════════════════════════════════════════════════════
# Test 5: duplicate proposal rejected
# ═══════════════════════════════════════════════════════════════════════


def test_duplicate_proposal_rejected():
    svc, _ = _make_service(_mock_row("accepted_candidate"))
    svc.propose_from_accepted("crule_005", created_by="admin", rationale="First")
    with pytest.raises(DuplicateProposalError, match="crule_005"):
        svc.propose_from_accepted("crule_005", created_by="admin", rationale="Second")


# ═══════════════════════════════════════════════════════════════════════
# Test 6: proposal preserves candidate_rule_id
# ═══════════════════════════════════════════════════════════════════════


def test_proposal_preserves_candidate_rule_id():
    svc, _ = _make_service(_mock_row("accepted_candidate"))
    proposal = svc.propose_from_accepted("crule_006", created_by="admin", rationale="test")
    assert proposal.candidate_rule_id == "crule_006"


# ═══════════════════════════════════════════════════════════════════════
# Test 7: proposal preserves source_refs from CandidateRule
# ═══════════════════════════════════════════════════════════════════════


def test_proposal_preserves_source_refs():
    svc, _ = _make_service(
        _mock_row("accepted_candidate", source_refs_json='["review:r1","lesson:L1","reviewer:alice"]')
    )
    proposal = svc.propose_from_accepted("crule_007", created_by="admin", rationale="test")
    assert "review:r1" in proposal.source_refs
    assert "lesson:L1" in proposal.source_refs
    assert "reviewer:alice" in proposal.source_refs
    assert "candidate_rule:crule_007" in proposal.source_refs


# ═══════════════════════════════════════════════════════════════════════
# Test 8: proposal does not modify Pack policy
# ═══════════════════════════════════════════════════════════════════════


def test_proposal_does_not_modify_pack_policy():
    """PolicyProposal creation must not touch packs/ files."""
    svc, _ = _make_service(_mock_row("accepted_candidate"))
    proposal = svc.propose_from_accepted("crule_008", created_by="admin", rationale="test")
    # No file I/O, no import of pack modules
    assert proposal.status == "draft"


# ═══════════════════════════════════════════════════════════════════════
# Test 9: proposal does not affect RiskEngine
# ═══════════════════════════════════════════════════════════════════════


def test_proposal_does_not_affect_risk_engine():
    """PolicyProposal must not import or modify RiskEngine."""
    import inspect
    from domains.candidate_rules import policy_proposal as mod

    src = inspect.getsource(mod)
    import_lines = [l for l in src.splitlines() if l.strip().startswith(("from ", "import "))]
    assert "RiskEngine" not in "\n".join(import_lines)
    assert "governance.risk_engine" not in "\n".join(import_lines)


# ═══════════════════════════════════════════════════════════════════════
# Test 10: proposal is not active Policy
# ═══════════════════════════════════════════════════════════════════════


def test_proposal_is_not_active_policy():
    svc, _ = _make_service(_mock_row("accepted_candidate"))
    proposal = svc.propose_from_accepted("crule_009", created_by="admin", rationale="test")
    assert proposal.status == "draft"
    assert proposal.status != "active"


# ═══════════════════════════════════════════════════════════════════════
# Test 11: no ExecutionRequest/Receipt
# ═══════════════════════════════════════════════════════════════════════


def test_proposal_no_execution_side_effects():
    import inspect
    from domains.candidate_rules import policy_proposal as mod

    src = inspect.getsource(mod)
    import_lines = [l for l in src.splitlines() if l.strip().startswith(("from ", "import "))]
    forbidden = ["ExecutionRequest", "ExecutionReceipt"]
    for word in forbidden:
        assert word not in "\n".join(import_lines), f"Forbidden import: {word}"


# ═══════════════════════════════════════════════════════════════════════
# Test 12: no broker/order/trade/shell/MCP/IDE
# ═══════════════════════════════════════════════════════════════════════


def test_proposal_no_broker_imports():
    import inspect
    from domains.candidate_rules import policy_proposal as mod

    src = inspect.getsource(mod)
    import_lines = [l for l in src.splitlines() if l.strip().startswith(("from ", "import "))]
    forbidden = ["broker", "place_order", "execute_trade", "shell", "MCP"]
    for word in forbidden:
        assert word not in "\n".join(import_lines), f"Forbidden import: {word}"


# ═══════════════════════════════════════════════════════════════════════
# Test 13: PolicyProposal model validation
# ═══════════════════════════════════════════════════════════════════════


def test_policy_proposal_requires_candidate_rule_id():
    with pytest.raises(ValueError, match="candidate_rule_id"):
        PolicyProposal(candidate_rule_id="")


def test_policy_proposal_invalid_status():
    with pytest.raises(ValueError, match="Unsupported proposal status"):
        PolicyProposal(candidate_rule_id="crule_x", status="active")


def test_policy_proposal_defaults():
    proposal = PolicyProposal(candidate_rule_id="crule_x")
    assert proposal.status == "draft"
    assert proposal.id.startswith("pprop")

"""CandidateRule Review Service — unit tests for human review path."""

import pytest
from unittest.mock import MagicMock

from domains.candidate_rules.review_service import (
    CandidateRuleReviewService,
    InvalidReviewTransition,
    CandidateRuleNotFound,
)
from domains.candidate_rules.repository import CandidateRuleRepository


# ── Helpers ──────────────────────────────────────────────────────────


def _mock_row(status="draft", source_refs=None):
    row = MagicMock()
    row.status = status
    row.source_refs_json = '["review:r1","lesson:L1"]' if source_refs is None else source_refs
    return row


def _make_service(db=None):
    if db is None:
        db = MagicMock()
    repo = CandidateRuleRepository(db)
    return CandidateRuleReviewService(repo), repo


# ═══════════════════════════════════════════════════════════════════════
# Test 1: draft → under_review
# ═══════════════════════════════════════════════════════════════════════


def test_submit_for_review_from_draft():
    svc, repo = _make_service()
    row = _mock_row("draft")
    repo.get = MagicMock(return_value=row)

    svc.submit_for_review("crule_001", reviewer_id="alice")

    assert row.status == "under_review"
    assert "reviewer:alice" in row.source_refs_json


# ═══════════════════════════════════════════════════════════════════════
# Test 2: draft → rejected (direct)
# ═══════════════════════════════════════════════════════════════════════


def test_reject_from_draft():
    svc, repo = _make_service()
    row = _mock_row("draft")
    repo.get = MagicMock(return_value=row)

    svc.reject_candidate("crule_002", reviewer_id="bob", rationale="Not actionable")

    assert row.status == "rejected"
    assert "reviewer:bob" in row.source_refs_json
    assert "review_rationale:Not actionable" in row.source_refs_json


# ═══════════════════════════════════════════════════════════════════════
# Test 3: under_review → accepted_candidate
# ═══════════════════════════════════════════════════════════════════════


def test_accept_from_under_review():
    svc, repo = _make_service()
    row = _mock_row("under_review")
    repo.get = MagicMock(return_value=row)

    svc.accept_candidate("crule_003", reviewer_id="carol", rationale="Clear pattern, ready for policy")

    assert row.status == "accepted_candidate"


# ═══════════════════════════════════════════════════════════════════════
# Test 4: under_review → rejected
# ═══════════════════════════════════════════════════════════════════════


def test_reject_from_under_review():
    svc, repo = _make_service()
    row = _mock_row("under_review")
    repo.get = MagicMock(return_value=row)

    svc.reject_candidate("crule_004", reviewer_id="dan", rationale="No pattern detected")

    assert row.status == "rejected"


# ═══════════════════════════════════════════════════════════════════════
# Test 5: accepted_candidate cannot transition → no Policy promotion
# ═══════════════════════════════════════════════════════════════════════


def test_accepted_candidate_cannot_transition():
    svc, repo = _make_service()
    row = _mock_row("accepted_candidate")
    repo.get = MagicMock(return_value=row)

    with pytest.raises(InvalidReviewTransition):
        svc.accept_candidate("crule_005", reviewer_id="eve", rationale="double accept")

    with pytest.raises(InvalidReviewTransition):
        svc.reject_candidate("crule_005", reviewer_id="eve", rationale="changed mind")

    with pytest.raises(InvalidReviewTransition):
        svc.submit_for_review("crule_005", reviewer_id="eve")


# ═══════════════════════════════════════════════════════════════════════
# Test 6: accepted_candidate does NOT auto-promote Policy
# ═══════════════════════════════════════════════════════════════════════


def test_accept_does_not_create_policy():
    """accept_candidate only changes status — no Policy, no execution, no broker."""
    svc, repo = _make_service()
    row = _mock_row("under_review")
    repo.get = MagicMock(return_value=row)

    svc.accept_candidate("crule_006", reviewer_id="frank", rationale="valid")

    assert row.status == "accepted_candidate"
    # No Policy table, no execution, no broker calls
    assert not hasattr(repo, "create_policy")


# ═══════════════════════════════════════════════════════════════════════
# Test 7: rejected cannot become accepted_candidate
# ═══════════════════════════════════════════════════════════════════════


def test_rejected_cannot_become_accepted():
    svc, repo = _make_service()
    row = _mock_row("rejected")
    repo.get = MagicMock(return_value=row)

    with pytest.raises(InvalidReviewTransition):
        svc.accept_candidate("crule_007", reviewer_id="grace", rationale="reconsidered")


# ═══════════════════════════════════════════════════════════════════════
# Test 8: source_refs preserved across transitions
# ═══════════════════════════════════════════════════════════════════════


def test_source_refs_preserved():
    svc, repo = _make_service()
    row = _mock_row("draft", source_refs='["review:r1","lesson:L1"]')
    repo.get = MagicMock(return_value=row)

    svc.submit_for_review("crule_008", reviewer_id="hank")

    assert "review:r1" in row.source_refs_json
    assert "lesson:L1" in row.source_refs_json
    assert "reviewer:hank" in row.source_refs_json


# ═══════════════════════════════════════════════════════════════════════
# Test 9: lesson_ids preserved (via ORM, not source_refs)
# ═══════════════════════════════════════════════════════════════════════


def test_lesson_ids_preserved():
    svc, repo = _make_service()
    row = _mock_row("draft")
    row.lesson_ids_json = '["lesson_001","lesson_002"]'
    repo.get = MagicMock(return_value=row)

    svc.submit_for_review("crule_009", reviewer_id="iris")

    # lesson_ids_json should be unchanged by review transition
    assert "lesson_001" in row.lesson_ids_json
    assert "lesson_002" in row.lesson_ids_json


# ═══════════════════════════════════════════════════════════════════════
# Test 10: invalid target status rejected
# ═══════════════════════════════════════════════════════════════════════


def test_invalid_transition_raises():
    svc, repo = _make_service()
    row = _mock_row("draft")
    repo.get = MagicMock(return_value=row)

    with pytest.raises(InvalidReviewTransition):
        # draft → accepted_candidate is NOT allowed (must go through under_review)
        svc._transition("crule_010", "accepted_candidate", reviewer_id="jack", note="skip review")


# ═══════════════════════════════════════════════════════════════════════
# Test 11: not found raises
# ═══════════════════════════════════════════════════════════════════════


def test_not_found_raises():
    svc, repo = _make_service()
    repo.get = MagicMock(return_value=None)

    with pytest.raises(CandidateRuleNotFound):
        svc.submit_for_review("crule_missing", reviewer_id="ken")


# ═══════════════════════════════════════════════════════════════════════
# Test 12: no broker/order/trade in review service
# ═══════════════════════════════════════════════════════════════════════


def test_review_service_no_broker_imports():
    import inspect
    from domains.candidate_rules import review_service as mod

    src = inspect.getsource(mod)
    import_lines = [l for l in src.splitlines() if l.strip().startswith(("from ", "import "))]
    forbidden = ["broker", "place_order", "execute_trade", "ExecutionRequest", "ExecutionReceipt"]
    for word in forbidden:
        assert word not in "\n".join(import_lines), f"Forbidden import: {word}"


# ═══════════════════════════════════════════════════════════════════════
# Test 13: repository get method works
# ═══════════════════════════════════════════════════════════════════════


def test_repository_get():
    from domains.candidate_rules.repository import CandidateRuleRepository

    db = MagicMock()
    repo = CandidateRuleRepository(db)
    mock_row = MagicMock()
    db.get.return_value = mock_row

    result = repo.get("crule_test")
    assert result is mock_row
    db.get.assert_called_once()


def test_repository_update_status():
    from domains.candidate_rules.repository import CandidateRuleRepository

    db = MagicMock()
    repo = CandidateRuleRepository(db)
    mock_row = MagicMock()
    mock_row.status = "draft"
    db.get.return_value = mock_row

    result = repo.update_status("crule_test", "under_review")
    assert result is mock_row
    assert mock_row.status == "under_review"

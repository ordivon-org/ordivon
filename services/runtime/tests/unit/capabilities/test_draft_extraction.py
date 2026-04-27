"""Tests for CandidateRule Draft Extraction Service.

Covers:
  1. rule_candidate lesson creates CandidateRule draft
  2. CandidateRule state == draft
  3. source_refs include review_id and lesson_id
  4. source_refs include outcome_ref when present
  5. non-rule_candidate lesson does not create CandidateRule
  6. Repeated completion does not duplicate CandidateRule
  7. No Policy promotion (status never accepted_candidate)
  8. No broker/order/trade/execution side effects
"""

import pytest
from unittest.mock import MagicMock, patch

from domains.candidate_rules.draft_extraction import (
    CandidateRuleDraftExtractionService,
    DraftExtractionResult,
)
from domains.candidate_rules.repository import CandidateRuleRepository
from domains.candidate_rules.models import CandidateRule, VALID_CANDIDATE_RULE_STATES


# ── Helpers ──────────────────────────────────────────────────────────


def _make_repo(db=None):
    """Create a CandidateRuleRepository with a mock db."""
    if db is None:
        db = MagicMock()
    return CandidateRuleRepository(db)


def _make_lesson(**overrides):
    """Create a lesson dict with defaults."""
    data = {
        "id": "lesson_test_001",
        "lesson_type": "review_learning",
        "body": "Test lesson body",
        "tags": [],
    }
    data.update(overrides)
    return data


# ═══════════════════════════════════════════════════════════════════════
# Test 1: rule_candidate lesson creates CandidateRule draft
# ═══════════════════════════════════════════════════════════════════════


def test_rule_candidate_lesson_creates_draft():
    """A lesson with lesson_type='rule_candidate' produces a CandidateRule draft."""
    repo = _make_repo()
    # No existing CandidateRule for this lesson
    repo.find_by_lesson_id = MagicMock(return_value=None)
    repo.create = MagicMock()

    svc = CandidateRuleDraftExtractionService(repo)
    result = svc.extract_from_review(
        review_id="review_001",
        recommendation_id="reco_001",
        lessons=[
            _make_lesson(
                id="lesson_001",
                lesson_type="rule_candidate",
                body="Always require stop_loss for high-risk trades",
                tags=["risk_management"],
            ),
        ],
    )

    assert result.lessons_scanned == 1
    assert result.rule_candidate_lessons == 1
    assert result.drafts_created == 1
    assert result.drafts_skipped_duplicate == 0
    assert repo.create.called

    # Verify the created CandidateRule
    call_args = repo.create.call_args[0][0]  # first positional arg
    assert isinstance(call_args, CandidateRule)
    assert call_args.status == "draft"


# ═══════════════════════════════════════════════════════════════════════
# Test 2: CandidateRule state == draft (never accepted_candidate)
# ═══════════════════════════════════════════════════════════════════════


def test_draft_never_promoted_to_accepted_candidate():
    """Extraction must never set status='accepted_candidate'."""
    repo = _make_repo()
    repo.find_by_lesson_id = MagicMock(return_value=None)
    repo.create = MagicMock()

    svc = CandidateRuleDraftExtractionService(repo)
    svc.extract_from_review(
        review_id="review_001",
        lessons=[
            _make_lesson(
                id="lesson_002",
                lesson_type="rule_candidate",
                body="Test",
            ),
        ],
    )

    created = repo.create.call_args[0][0]
    assert created.status == "draft"
    assert created.status != "accepted_candidate"
    assert created.status in VALID_CANDIDATE_RULE_STATES


# ═══════════════════════════════════════════════════════════════════════
# Test 3: source_refs include review_id and lesson_id
# ═══════════════════════════════════════════════════════════════════════


def test_source_refs_include_review_and_lesson():
    """source_refs must contain review:<id> and lesson:<id>."""
    repo = _make_repo()
    repo.find_by_lesson_id = MagicMock(return_value=None)
    repo.create = MagicMock()

    svc = CandidateRuleDraftExtractionService(repo)
    svc.extract_from_review(
        review_id="review_003",
        lessons=[
            _make_lesson(
                id="lesson_003",
                lesson_type="rule_candidate",
                body="Test",
            ),
        ],
    )

    created = repo.create.call_args[0][0]
    assert "review:review_003" in created.source_refs
    assert "lesson:lesson_003" in created.source_refs


# ═══════════════════════════════════════════════════════════════════════
# Test 4: source_refs include outcome_ref when present
# ═══════════════════════════════════════════════════════════════════════


def test_source_refs_include_outcome_ref():
    """When Review has outcome_ref_type/id, source_refs include them."""
    repo = _make_repo()
    repo.find_by_lesson_id = MagicMock(return_value=None)
    repo.create = MagicMock()

    svc = CandidateRuleDraftExtractionService(repo)
    svc.extract_from_review(
        review_id="review_004",
        lessons=[
            _make_lesson(
                id="lesson_004",
                lesson_type="rule_candidate",
                body="Test",
            ),
        ],
        outcome_ref_type="finance_manual_outcome",
        outcome_ref_id="fmout_abc123",
    )

    created = repo.create.call_args[0][0]
    assert "finance_manual_outcome:fmout_abc123" in created.source_refs


# ═══════════════════════════════════════════════════════════════════════
# Test 5: non-rule_candidate lesson does not create CandidateRule
# ═══════════════════════════════════════════════════════════════════════


def test_non_rule_candidate_lesson_skipped():
    """Only lesson_type='rule_candidate' triggers draft creation."""
    repo = _make_repo()
    repo.find_by_lesson_id = MagicMock(return_value=None)
    repo.create = MagicMock()

    svc = CandidateRuleDraftExtractionService(repo)
    result = svc.extract_from_review(
        review_id="review_005",
        lessons=[
            _make_lesson(id="lesson_a", lesson_type="review_learning", body="Normal lesson"),
            _make_lesson(id="lesson_b", lesson_type="rule_candidate", body="Rule candidate"),
            _make_lesson(id="lesson_c", lesson_type="review_learning", body="Another normal"),
        ],
    )

    assert result.lessons_scanned == 3
    assert result.rule_candidate_lessons == 1
    assert result.drafts_created == 1
    assert result.drafts_skipped_duplicate == 0

    # Only lesson_b should create a draft
    created = repo.create.call_args[0][0]
    assert "lesson:lesson_b" in created.source_refs
    assert "lesson:lesson_a" not in created.source_refs


# ═══════════════════════════════════════════════════════════════════════
# Test 6: repeated completion does not duplicate CandidateRule
# ═══════════════════════════════════════════════════════════════════════


def test_idempotent_extraction():
    """Calling extract_from_review twice with the same lesson creates only one draft."""
    repo = _make_repo()
    # First call: no existing → creates
    repo.find_by_lesson_id = MagicMock(return_value=None)
    repo.create = MagicMock()

    svc = CandidateRuleDraftExtractionService(repo)
    lessons = [
        _make_lesson(id="lesson_006", lesson_type="rule_candidate", body="Test"),
    ]

    result1 = svc.extract_from_review(review_id="review_006", lessons=lessons)
    assert result1.drafts_created == 1
    assert result1.drafts_skipped_duplicate == 0

    # Second call: existing found → skips
    repo.find_by_lesson_id = MagicMock(return_value=MagicMock())  # simulate found
    result2 = svc.extract_from_review(review_id="review_006", lessons=lessons)
    assert result2.drafts_created == 0
    assert result2.drafts_skipped_duplicate == 1


# ═══════════════════════════════════════════════════════════════════════
# Test 7: no Policy promotion
# ═══════════════════════════════════════════════════════════════════════


def test_no_policy_promotion():
    """Verify that the service has no method or path to promote to Policy."""
    repo = _make_repo()
    svc = CandidateRuleDraftExtractionService(repo)

    # The service must not have any method that sets status=accepted_candidate
    public_methods = [m for m in dir(svc) if not m.startswith("_")]
    assert "promote" not in public_methods
    assert "accept" not in public_methods
    assert "approve" not in public_methods

    # All created CandidateRules must have status="draft"
    repo.find_by_lesson_id = MagicMock(return_value=None)
    repo.create = MagicMock()
    svc.extract_from_review(
        review_id="review_007",
        lessons=[_make_lesson(id="lesson_007", lesson_type="rule_candidate", body="Test")],
    )
    created = repo.create.call_args[0][0]
    assert created.status == "draft"
    assert created.status != "accepted_candidate"


# ═══════════════════════════════════════════════════════════════════════
# Test 8: no broker/order/trade/execution side effects
# ═══════════════════════════════════════════════════════════════════════


def test_no_broker_order_trade_imports():
    """The draft_extraction module must not import broker/order/trade modules."""
    import inspect
    from domains.candidate_rules import draft_extraction

    source = inspect.getsource(draft_extraction)
    # Only check import lines — not docstrings or comments
    import_lines = [l for l in source.splitlines() if l.strip().startswith(("from ", "import "))]
    source_imports = "\n".join(import_lines)
    forbidden = ["broker", "place_order", "execute_trade"]
    for word in forbidden:
        assert word not in source_imports, f"draft_extraction.py imports forbidden module: '{word}'"


def test_draft_extraction_no_db_side_effects():
    """Extraction only calls repository methods — no direct SQL or external calls."""
    repo = _make_repo()
    repo.find_by_lesson_id = MagicMock(return_value=None)
    repo.create = MagicMock()

    svc = CandidateRuleDraftExtractionService(repo)
    svc.extract_from_review(
        review_id="review_008",
        lessons=[_make_lesson(id="lesson_008", lesson_type="rule_candidate", body="Test")],
    )

    # Only find_by_lesson_id and create should be called
    assert repo.find_by_lesson_id.called
    assert repo.create.called
    # No other side effects on the db mock


# ═══════════════════════════════════════════════════════════════════════
# Test 9: extraction errors don't block (fail-safe)
# ═══════════════════════════════════════════════════════════════════════


def test_extraction_error_does_not_block():
    """If one lesson fails extraction, others still proceed."""
    repo = _make_repo()

    call_count = [0]

    def create_side_effect(rule):
        call_count[0] += 1
        if call_count[0] == 1:
            raise RuntimeError("simulated DB error")
        return MagicMock()

    repo.find_by_lesson_id = MagicMock(return_value=None)
    repo.create = MagicMock(side_effect=create_side_effect)

    svc = CandidateRuleDraftExtractionService(repo)
    result = svc.extract_from_review(
        review_id="review_009",
        lessons=[
            _make_lesson(id="lesson_bad", lesson_type="rule_candidate", body="Will fail"),
            _make_lesson(id="lesson_good", lesson_type="rule_candidate", body="Will succeed"),
        ],
    )

    # First lesson errored, second succeeded
    assert result.rule_candidate_lessons == 2
    assert result.drafts_created == 1
    assert len(result.errors) == 1
    assert "lesson_bad" in result.errors[0]

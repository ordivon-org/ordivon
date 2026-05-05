"""Tests for CheckerMaturityStateMachine — invariant enforcement + red-team."""

import pytest
from domains.checker_maturity import (
    CheckerMaturityRecord,
    CheckerMaturityStateMachine,
    MaturityLevel,
    InvalidTransitionError,
    MissingEvidenceError,
    SelfPromotionError,
)


def make_record(level=MaturityLevel.DRAFT, author="alice", changed_by="alice",
                evidence=(), notes=""):
    return CheckerMaturityRecord(
        checker_id="test-checker",
        maturity=level,
        author=author,
        changed_by=changed_by,
        changed_at="2026-05-04T00:00:00Z",
        evidence_refs=evidence,
        notes=notes,
    )


class TestValidTransitions:
    """Happy path: allowed transitions succeed with correct evidence."""

    def test_draft_to_shadow_tested_independent(self):
        rec = make_record(MaturityLevel.DRAFT, author="alice")
        new = CheckerMaturityStateMachine.transition(
            rec, MaturityLevel.SHADOW_TESTED,
            changed_by="bob",  # different from author
            evidence_refs=("shadow-log:2026-05-04",),
        )
        assert new.maturity == MaturityLevel.SHADOW_TESTED
        assert new.changed_by == "bob"

    def test_shadow_tested_to_red_teamed(self):
        rec = make_record(MaturityLevel.SHADOW_TESTED, author="alice")
        new = CheckerMaturityStateMachine.transition(
            rec, MaturityLevel.RED_TEAMED,
            changed_by="bob",
            evidence_refs=("red-team-review:2026-05-04",),
        )
        assert new.maturity == MaturityLevel.RED_TEAMED

    def test_red_teamed_to_active_with_owner(self):
        rec = make_record(MaturityLevel.RED_TEAMED, author="alice")
        new = CheckerMaturityStateMachine.transition(
            rec, MaturityLevel.ACTIVE,
            changed_by="bob",
            evidence_refs=("owner-approval:2026-05-04", "shadow-assessment:PASS"),
        )
        assert new.maturity == MaturityLevel.ACTIVE

    def test_active_to_draft_rollback_self_allowed(self):
        """Owner can roll back their own gate — self-promotion check
        only applies to promotion, not demotion."""
        rec = make_record(MaturityLevel.ACTIVE, author="alice")
        new = CheckerMaturityStateMachine.transition(
            rec, MaturityLevel.DRAFT,
            changed_by="alice",  # same as author — allowed for rollback
            evidence_refs=("rollback-receipt:2026-05-04",),
        )
        assert new.maturity == MaturityLevel.DRAFT


class TestInvalidTransitions:
    """Every forbidden transition is tested."""

    def test_draft_to_active_skips_stages(self):
        rec = make_record(MaturityLevel.DRAFT)
        with pytest.raises(InvalidTransitionError) as exc:
            CheckerMaturityStateMachine.transition(
                rec, MaturityLevel.ACTIVE, changed_by="bob",
                evidence_refs=("approval",),
            )
        assert "draft" in str(exc.value).lower()
        assert "active" in str(exc.value).lower()

    def test_shadow_tested_to_active_skips_red_team(self):
        rec = make_record(MaturityLevel.SHADOW_TESTED)
        with pytest.raises(InvalidTransitionError):
            CheckerMaturityStateMachine.transition(
                rec, MaturityLevel.ACTIVE, changed_by="bob",
            )

    def test_active_to_red_teamed_not_allowed(self):
        rec = make_record(MaturityLevel.ACTIVE)
        with pytest.raises(InvalidTransitionError):
            CheckerMaturityStateMachine.transition(
                rec, MaturityLevel.RED_TEAMED, changed_by="bob",
            )

    def test_archived_is_terminal(self):
        rec = make_record(MaturityLevel.ARCHIVED)
        assert CheckerMaturityStateMachine.is_terminal(rec.maturity)
        with pytest.raises(InvalidTransitionError):
            CheckerMaturityStateMachine.transition(
                rec, MaturityLevel.ACTIVE, changed_by="bob",
            )

    def test_deprecated_to_active_not_allowed(self):
        rec = make_record(MaturityLevel.DEPRECATED)
        with pytest.raises(InvalidTransitionError):
            CheckerMaturityStateMachine.transition(
                rec, MaturityLevel.ACTIVE, changed_by="bob",
            )


class TestSelfPromotionPrevention:
    """Rust RFC pattern: author cannot self-promote."""

    def test_draft_promotion_self_blocked(self):
        rec = make_record(MaturityLevel.DRAFT, author="alice")
        with pytest.raises(SelfPromotionError):
            CheckerMaturityStateMachine.transition(
                rec, MaturityLevel.SHADOW_TESTED,
                changed_by="alice",  # same as author
                evidence_refs=("shadow-log:2026-05-04",),
            )

    def test_red_teamed_self_promotion_blocked(self):
        rec = make_record(MaturityLevel.RED_TEAMED, author="alice")
        with pytest.raises(SelfPromotionError):
            CheckerMaturityStateMachine.transition(
                rec, MaturityLevel.ACTIVE,
                changed_by="alice",
                evidence_refs=("owner-approval", "shadow-assessment"),
            )

    def test_rollback_self_allowed(self):
        """Self-promotion check only blocks promotion, not demotion."""
        rec = make_record(MaturityLevel.ACTIVE, author="alice")
        new = CheckerMaturityStateMachine.transition(
            rec, MaturityLevel.DRAFT,
            changed_by="alice",
            evidence_refs=("rollback-receipt",),
        )
        assert new.maturity == MaturityLevel.DRAFT


class TestEvidenceEnforcement:
    """K8s PRR pattern: promotion requires specific evidence."""

    def test_promotion_without_evidence_blocked(self):
        rec = make_record(MaturityLevel.DRAFT, author="alice")
        with pytest.raises(MissingEvidenceError):
            CheckerMaturityStateMachine.transition(
                rec, MaturityLevel.SHADOW_TESTED,
                changed_by="bob",
                evidence_refs=(),  # no evidence
            )

    def test_active_promotion_requires_owner_and_shadow(self):
        rec = make_record(MaturityLevel.RED_TEAMED, author="alice")
        # Missing shadow-assessment evidence
        with pytest.raises(MissingEvidenceError):
            CheckerMaturityStateMachine.transition(
                rec, MaturityLevel.ACTIVE,
                changed_by="bob",
                evidence_refs=(),  # needs owner_approval + shadow_assessment
            )


class TestInvariants:
    """Structural invariants of the maturity model."""

    def test_record_immutability(self):
        rec = make_record()
        with pytest.raises(Exception):  # dataclass frozen
            rec.maturity = MaturityLevel.ACTIVE  # type: ignore

    def test_record_requires_checker_id(self):
        with pytest.raises(ValueError, match="checker_id"):
            CheckerMaturityRecord(
                checker_id="", maturity=MaturityLevel.DRAFT,
                author="alice", changed_by="alice",
                changed_at="2026-01-01T00:00:00Z",
                evidence_refs=(),
            )

    def test_record_requires_author(self):
        with pytest.raises(ValueError, match="author"):
            CheckerMaturityRecord(
                checker_id="test", maturity=MaturityLevel.DRAFT,
                author="", changed_by="alice",
                changed_at="2026-01-01T00:00:00Z",
                evidence_refs=(),
            )

    def test_allowed_transitions_from_every_level(self):
        """Every level should have a defined set of allowed transitions."""
        for level in MaturityLevel:
            allowed = CheckerMaturityStateMachine.allowed_transitions_from(level)
            assert isinstance(allowed, frozenset)
            # Archived must be terminal
            if level == MaturityLevel.ARCHIVED:
                assert len(allowed) == 0

    def test_draft_rejects_same_level(self):
        rec = make_record(MaturityLevel.DRAFT)
        with pytest.raises(InvalidTransitionError):
            CheckerMaturityStateMachine.transition(
                rec, MaturityLevel.DRAFT,
                changed_by="bob",
                evidence_refs=("evidence",),
            )

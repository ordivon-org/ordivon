"""FinanceManualOutcome tests — verdict validation, source constraints, required fields."""
import pytest

from domains.finance_outcome.models import (
    FinanceManualOutcome,
    VALID_OUTCOME_SOURCES,
    VALID_OUTCOME_VERDICTS,
)


# ═══════════════════════════════════════════════════════════════════════
# D2.1 — Valid verdicts accepted
# ═══════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("verdict", sorted(VALID_OUTCOME_VERDICTS))
def test_valid_verdict_accepted(verdict):
    """All verdicts in VALID_OUTCOME_VERDICTS must be acceptable."""
    outcome = FinanceManualOutcome(
        decision_intake_id="intake_001",
        execution_receipt_id="exrcpt_001",
        verdict=verdict,
    )
    assert outcome.verdict == verdict
    assert outcome.outcome_source == "manual"


def test_invalid_verdict_rejected():
    """Unknown verdict must raise ValueError."""
    with pytest.raises(ValueError, match="Unsupported verdict"):
        FinanceManualOutcome(
            decision_intake_id="intake_001",
            execution_receipt_id="exrcpt_001",
            verdict="win",  # not a valid verdict
        )


# ═══════════════════════════════════════════════════════════════════════
# D2.2 — outcome_source must be manual
# ═══════════════════════════════════════════════════════════════════════

def test_outcome_source_defaults_to_manual():
    outcome = FinanceManualOutcome(
        decision_intake_id="intake_001",
        execution_receipt_id="exrcpt_001",
        verdict="validated",
    )
    assert outcome.outcome_source == "manual"


def test_outcome_source_must_be_in_valid_set():
    """Only 'manual' is valid — anything else raises."""
    with pytest.raises(ValueError, match="Unsupported outcome_source"):
        FinanceManualOutcome(
            decision_intake_id="intake_001",
            execution_receipt_id="exrcpt_001",
            verdict="validated",
            outcome_source="automated",  # not allowed
        )


def test_valid_outcome_sources_contains_only_manual():
    assert VALID_OUTCOME_SOURCES == {"manual"}


# ═══════════════════════════════════════════════════════════════════════
# D2.3 — Required fields
# ═══════════════════════════════════════════════════════════════════════

def test_missing_decision_intake_id_raises():
    with pytest.raises(ValueError, match="decision_intake_id"):
        FinanceManualOutcome(
            decision_intake_id="",
            execution_receipt_id="exrcpt_001",
            verdict="validated",
        )


def test_missing_execution_receipt_id_raises():
    with pytest.raises(ValueError, match="execution_receipt_id"):
        FinanceManualOutcome(
            decision_intake_id="intake_001",
            execution_receipt_id="",
            verdict="validated",
        )


# ═══════════════════════════════════════════════════════════════════════
# D2.4 — plan_followed default
# ═══════════════════════════════════════════════════════════════════════

def test_plan_followed_defaults_to_false():
    outcome = FinanceManualOutcome(
        decision_intake_id="intake_001",
        execution_receipt_id="exrcpt_001",
        verdict="validated",
    )
    assert outcome.plan_followed is False


def test_plan_followed_can_be_true():
    outcome = FinanceManualOutcome(
        decision_intake_id="intake_001",
        execution_receipt_id="exrcpt_001",
        verdict="validated",
        plan_followed=True,
    )
    assert outcome.plan_followed is True


# ═══════════════════════════════════════════════════════════════════════
# D2.5 — ID generation
# ═══════════════════════════════════════════════════════════════════════

def test_outcome_id_generated_with_fmout_prefix():
    outcome = FinanceManualOutcome(
        decision_intake_id="intake_001",
        execution_receipt_id="exrcpt_001",
        verdict="validated",
    )
    assert outcome.id.startswith("fmout")


# ═══════════════════════════════════════════════════════════════════════
# D2.6 — observed_outcome and variance_summary optional
# ═══════════════════════════════════════════════════════════════════════

def test_observed_outcome_defaults_to_empty():
    outcome = FinanceManualOutcome(
        decision_intake_id="intake_001",
        execution_receipt_id="exrcpt_001",
        verdict="validated",
    )
    assert outcome.observed_outcome == ""


def test_variance_summary_defaults_to_none():
    outcome = FinanceManualOutcome(
        decision_intake_id="intake_001",
        execution_receipt_id="exrcpt_001",
        verdict="validated",
    )
    assert outcome.variance_summary is None

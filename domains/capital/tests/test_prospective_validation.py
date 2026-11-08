from datetime import UTC, date, datetime

import pytest

from ordivon_capital.research.prospective_validation import (
    aligned_post_decision_session_dates,
    evaluate_prospective_validation,
)


@pytest.fixture
def frozen() -> datetime:
    return datetime(2026, 9, 12, 14, 59, 29, tzinfo=UTC)


def _evaluate(frozen: datetime, sessions: dict[str, set[date]]) -> dict:
    return evaluate_prospective_validation(
        decision_boundary=frozen,
        session_timezone="America/New_York",
        series_dates=sessions,
    )


def test_same_or_prior_session_cannot_be_declared_post_decision(frozen: datetime) -> None:
    sessions = {symbol: {date(2026, 9, 11), date(2026, 9, 12)}
                for symbol in ("AAPL", "MSFT", "NVDA", "SPY")}
    result = _evaluate(frozen, sessions)
    assert result["standing"] == "WAITING_FOR_POST_DECISION_DATA"
    assert not result["postDecisionHoldoutAvailable"]
    assert not result["postDecisionSessionDatesAligned"]
    assert not result["marketSourceObservationVerified"]
    assert result["alignedCommonSessionDates"] == []


def test_one_missing_required_series_is_not_aligned(frozen: datetime) -> None:
    sessions = {
        "AAPL": {date(2026, 9, 14)},
        "MSFT": {date(2026, 9, 14)},
        "NVDA": {date(2026, 9, 14)},
        "SPY": set(),
    }
    assert _evaluate(frozen, sessions)["standing"] == "WAITING_FOR_POST_DECISION_DATA"


def test_all_series_aligned_is_calendar_evidence_not_market_evidence(
    frozen: datetime,
) -> None:
    sessions = {symbol: {date(2026, 9, 14), date(2026, 9, 15)}
                for symbol in ("AAPL", "MSFT", "NVDA", "SPY")}
    result = _evaluate(frozen, sessions)
    assert result["standing"] == "POST_DECISION_DATES_ALIGNED_SOURCE_UNVERIFIED"
    assert result["postDecisionSessionDatesAligned"]
    assert not result["postDecisionHoldoutAvailable"]
    assert not result["marketSourceObservationVerified"]
    assert result["firstAlignedCommonSessionDate"] == "2026-09-14"
    assert result["latestAlignedCommonSessionDate"] == "2026-09-15"


def test_calendar_intersection_does_not_union_incomplete_dates(frozen: datetime) -> None:
    sessions = {
        "AAPL": {date(2026, 9, 14), date(2026, 9, 15)},
        "MSFT": {date(2026, 9, 15)},
        "NVDA": {date(2026, 9, 14), date(2026, 9, 15)},
        "SPY": {date(2026, 9, 15)},
    }
    result = _evaluate(frozen, sessions)
    assert result["alignedCommonSessionDates"] == ["2026-09-15"]
    assert not result["postDecisionHoldoutAvailable"]


def test_far_future_unobserved_session_does_not_certify_holdout(
    frozen: datetime,
) -> None:
    """Negative evidence: a caller can invent far-future dates."""
    result = _evaluate(frozen, {"SPY": {date(2099, 1, 5)}})
    assert result["postDecisionSessionDatesAligned"]
    assert not result["postDecisionHoldoutAvailable"]
    assert not result["marketSourceObservationVerified"]


@pytest.mark.parametrize(
    "sessions",
    [
        {},
        {"SPY": ["2026-09-14"]},
        {"": {date(2026, 9, 14)}},
        {"SPY": {datetime(2026, 9, 14, tzinfo=UTC)}},
    ],
)
def test_invalid_calendar_claims_are_rejected(
    frozen: datetime, sessions: object,
) -> None:
    with pytest.raises(ValueError):
        _evaluate(frozen, sessions)  # type: ignore[arg-type]


def test_naive_decision_boundary_is_rejected() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        _evaluate(datetime(2026, 9, 12, 14, 59, 29), {"SPY": {date(2026, 9, 14)}})


def test_pure_calendar_helper_never_depends_on_source_attestation(frozen: datetime) -> None:
    assert aligned_post_decision_session_dates(
        decision_boundary=frozen,
        session_timezone="America/New_York",
        series_dates={"SPY": {date(2026, 9, 12), date(2026, 9, 14)}},
    ) == [date(2026, 9, 14)]

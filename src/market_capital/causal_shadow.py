from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo


def decision_session_date(decision_boundary: datetime, session_timezone: str) -> date:
    if decision_boundary.tzinfo is None:
        raise ValueError("decision boundary must be timezone-aware")
    return decision_boundary.astimezone(ZoneInfo(session_timezone)).date()


def common_post_decision_dates(
    *,
    decision_boundary: datetime,
    session_timezone: str,
    series_dates: dict[str, set[date]],
) -> list[date]:
    if not series_dates:
        raise ValueError("at least one required series is necessary")
    boundary_date = decision_session_date(decision_boundary, session_timezone)
    common = set.intersection(*(set(dates) for dates in series_dates.values()))
    return sorted(d for d in common if d > boundary_date)


def evaluate_causal_shadow(
    *,
    decision_boundary: datetime,
    session_timezone: str,
    series_dates: dict[str, set[date]],
) -> dict:
    eligible = common_post_decision_dates(
        decision_boundary=decision_boundary,
        session_timezone=session_timezone,
        series_dates=series_dates,
    )
    if not eligible:
        return {
            "gateImplemented": True,
            "causalEvidenceAvailable": False,
            "standing": "WAITING_FOR_POST_DECISION_DATA",
            "eligibleCommonSessionDates": [],
        }
    return {
        "gateImplemented": True,
        "causalEvidenceAvailable": True,
        "standing": "POST_DECISION_DATA_ADMITTED",
        "eligibleCommonSessionDates": [d.isoformat() for d in eligible],
        "firstEligibleCommonSessionDate": eligible[0].isoformat(),
        "latestEligibleCommonSessionDate": eligible[-1].isoformat(),
    }

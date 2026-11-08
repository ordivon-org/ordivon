"""A read-only post-decision *session-date* alignment check.

A date in a caller-supplied set is not an observed, source-authenticated
market bar. No source bytes, capture timestamps, release times, data rights,
or experiment provenance enter this pure function. It never certifies the
availability of a prospective financial holdout or strategy performance.
"""

from __future__ import annotations

from collections.abc import Mapping
from collections.abc import Set as AbstractSet
from datetime import date, datetime
from zoneinfo import ZoneInfo


def decision_session_date(decision_boundary: datetime, session_timezone: str) -> date:
    """Convert an aware decision instant into the market session calendar."""
    if decision_boundary.tzinfo is None or decision_boundary.utcoffset() is None:
        raise ValueError("decision boundary must be timezone-aware")
    return decision_boundary.astimezone(ZoneInfo(session_timezone)).date()


def aligned_post_decision_session_dates(
    *,
    decision_boundary: datetime,
    session_timezone: str,
    series_dates: Mapping[str, AbstractSet[date]],
) -> list[date]:
    """Intersect declared sessions strictly after the frozen decision date.

    The result is a set of *candidate calendar dates*, not authenticated
    observations. This is a pure Research predicate; market authority and
    capture provenance remain with Markets.
    """
    if not isinstance(series_dates, Mapping) or not series_dates:
        raise ValueError("at least one required series is necessary")
    if any(
        not isinstance(symbol, str) or not symbol
        or not isinstance(dates, AbstractSet)
        or any(type(day) is not date for day in dates)
        for symbol, dates in series_dates.items()
    ):
        raise ValueError("series dates require nonempty IDs and date-only sets")
    boundary_date = decision_session_date(decision_boundary, session_timezone)
    common = set.intersection(*(set(dates) for dates in series_dates.values()))
    return sorted(day for day in common if day > boundary_date)


def evaluate_prospective_validation(
    *,
    decision_boundary: datetime,
    session_timezone: str,
    series_dates: Mapping[str, AbstractSet[date]],
) -> dict:
    """Report date alignment without upgrading declarations to data evidence."""
    aligned = aligned_post_decision_session_dates(
        decision_boundary=decision_boundary,
        session_timezone=session_timezone,
        series_dates=series_dates,
    )
    result = {
        "componentId": "prospective-validation",
        "standing": (
            "POST_DECISION_DATES_ALIGNED_SOURCE_UNVERIFIED"
            if aligned else "WAITING_FOR_POST_DECISION_DATA"
        ),
        "postDecisionHoldoutAvailable": False,
        "postDecisionSessionDatesAligned": bool(aligned),
        "marketSourceObservationVerified": False,
        "alignedCommonSessionDates": [day.isoformat() for day in aligned],
    }
    if aligned:
        result["firstAlignedCommonSessionDate"] = aligned[0].isoformat()
        result["latestAlignedCommonSessionDate"] = aligned[-1].isoformat()
    return result

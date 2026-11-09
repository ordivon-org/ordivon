"""Pure time-budget arbitration for one bounded Harness Agent Run.

Monotonic and wall-clock timestamps are explicit values, not implicit reads.
The caller creates the actual RunDeadline with its existing monotonic clock.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SelectedRunDeadline:
    expires_at_ms: int
    remaining_ms: int
    total_wall_budget_ms: int
    source: str
    assignment_remaining_ms: int | None


def select_run_deadline(
    *,
    active_remaining_ms: int,
    prior_elapsed_ms: int,
    observed_wall_time_ms: int,
    assignment_deadline_ms: int | None,
    started_at_ms: int,
    external_deadline_expires_at_ms: int | None,
) -> SelectedRunDeadline:
    """Keep the earliest effective deadline; preserve the historical tie order.

    Assignment wins an equality with active budget; an external deadline
    wins equality against the internal monotonic deadline. No effect occurs.
    """
    if observed_wall_time_ms < 0:
        raise ValueError("Harness wall clock returned a negative time")
    assignment_remaining_ms = (
        None
        if assignment_deadline_ms is None
        else max(0, assignment_deadline_ms - observed_wall_time_ms)
    )
    remaining_ms = active_remaining_ms
    source = "active_wall_time"
    if assignment_remaining_ms is not None and assignment_remaining_ms <= remaining_ms:
        remaining_ms = assignment_remaining_ms
        source = "assignment_deadline"
    expires_at_ms = started_at_ms + remaining_ms
    if external_deadline_expires_at_ms is not None and external_deadline_expires_at_ms <= expires_at_ms:
        expires_at_ms = external_deadline_expires_at_ms
        remaining_ms = max(0, expires_at_ms - started_at_ms)
        source = "external_deadline"
    return SelectedRunDeadline(
        expires_at_ms=expires_at_ms,
        remaining_ms=remaining_ms,
        total_wall_budget_ms=prior_elapsed_ms + remaining_ms,
        source=source,
        assignment_remaining_ms=assignment_remaining_ms,
    )

"""Shared read-only GitHub workflow observation primitives.

These qualify observed identities and page geometry, not provider atomicity,
test correctness, or permission to schedule, retry or delete work.
"""
from __future__ import annotations

import json
import subprocess
from datetime import datetime
from math import ceil
from statistics import mean, median
from typing import Any, Iterable


def instant(value: str | None) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.utcoffset() is not None else None


def seconds(start: str | None, end: str | None) -> float | None:
    a, b = instant(start), instant(end)
    if a is None or b is None:
        return None
    duration = (b - a).total_seconds()
    return duration if duration >= 0 else None


def summary(values: Iterable[float | None]) -> dict[str, float | int | None]:
    xs = sorted(float(x) for x in values if x is not None)
    if not xs:
        return {"count": 0, "mean": None, "median": None, "p95": None, "max": None}
    rank = ceil(0.95 * len(xs)) - 1
    return {
        "count": len(xs),
        "mean": round(mean(xs), 3),
        "median": round(median(xs), 3),
        "p95": round(xs[rank], 3),
        "max": round(max(xs), 3),
    }


# Bounded native observation; this is not a claim of atomic provider snapshot.
MAX_ATTEMPT_JOBS = 10_000


def run_identity(run: dict[str, Any]) -> tuple[int, int]:
    if not isinstance(run, dict):
        raise ValueError("malformed workflow run")
    run_id, attempt = run.get("id"), run.get("run_attempt")
    if type(run_id) is not int or run_id < 1 or type(attempt) is not int or attempt < 1:
        raise ValueError("unqualified workflow run or attempt identity")
    return run_id, attempt


def validate_attempt_jobs(
    rows: list[dict[str, Any]], run_id: int, attempt: int, seen: set[int],
) -> None:
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("malformed workflow attempt job")
        job_id = row.get("id")
        if (
            type(job_id) is not int or job_id < 1 or job_id in seen
            or type(row.get("run_id")) is not int or row["run_id"] != run_id
            or type(row.get("run_attempt")) is not int or row["run_attempt"] != attempt
        ):
            raise ValueError("unqualified or duplicate workflow attempt job")
        seen.add(job_id)


DEFAULT_REQUEST_TIMEOUT_SECONDS = 20
MAX_REQUEST_TIMEOUT_SECONDS = 300


class GitHubObservationTimeout(ValueError):
    """An incomplete provider observation, not a failed workflow result."""


def complete_page_geometry(total: int, observed: int, batch_size: int) -> bool:
    """Qualify the existing per_page=100 native pagination geometry."""
    return 0 <= observed <= total and batch_size == min(100, total - observed)


class GitHubWorkflowReader:
    def __init__(
        self, repo: str, *, request_timeout_seconds: float = DEFAULT_REQUEST_TIMEOUT_SECONDS
    ):
        if (
            type(request_timeout_seconds) not in (int, float)
            or not 0 < request_timeout_seconds <= MAX_REQUEST_TIMEOUT_SECONDS
        ):
            raise ValueError("request timeout must be finite positive and at most 300 seconds")
        self.repo = repo
        self.request_timeout_seconds = request_timeout_seconds

    def api(self, endpoint: str) -> Any:
        cmd = ["gh", "api", "-H", "Accept: application/vnd.github+json", endpoint]
        try:
            out = subprocess.run(
                cmd, check=True, text=True, capture_output=True,
                timeout=self.request_timeout_seconds,
            ).stdout
        except subprocess.TimeoutExpired:
            # Never parse partial output or automatically retry. This is a
            # per-request deadline, not a bound on the complete paged query.
            raise GitHubObservationTimeout("GitHub provider observation timed out") from None
        return json.loads(out)

    def collect_attempt_jobs(self, run_id: int, attempt: int) -> list[dict[str, Any]]:
        """Consume the provider's exact-attempt endpoint and page geometry."""
        rows: list[dict[str, Any]] = []
        seen: set[int] = set()
        total = None
        for page in range(1, (MAX_ATTEMPT_JOBS + 99) // 100 + 1):
            payload = self.api(
                f"repos/{self.repo}/actions/runs/{run_id}/attempts/{attempt}/jobs"
                f"?per_page=100&page={page}"
            )
            if not isinstance(payload, dict):
                raise ValueError("malformed workflow attempt jobs response")
            count, batch = payload.get("total_count"), payload.get("jobs")
            if (
                type(count) is not int or not 0 <= count <= MAX_ATTEMPT_JOBS
                or not isinstance(batch, list)
            ):
                raise ValueError("unqualified workflow attempt job count or rows")
            if total is None:
                total = count
            if total != count or not complete_page_geometry(count, len(rows), len(batch)):
                raise ValueError("incomplete or changing workflow attempt job pages")
            validate_attempt_jobs(batch, run_id, attempt, seen)
            rows.extend(batch)
            if len(rows) == total:
                return rows
        raise ValueError("workflow attempt job observation exceeds bound")

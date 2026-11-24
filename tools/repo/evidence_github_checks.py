"""Bounded read-only GitHub Check Run observation and receipt selection."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from urllib.parse import urlsplit

from ci_telemetry import Gh

MAX_CHECK_ROWS = 2000


def _provider_checks(gh: Gh, repo: str, sha: str) -> list[dict[str, Any]]:
    """Read all pages: a truncated or malformed listing grants no PASS."""
    rows: list[dict[str, Any]] = []
    page = 1
    expected_count = None
    while True:
        payload = gh.api(
            f"repos/{repo}/commits/{sha}/check-runs?filter=all&per_page=100&page={page}"
        )
        if (
            not isinstance(payload, dict)
            or type(payload.get("total_count")) is not int
            or not isinstance(payload.get("check_runs"), list)
        ):
            raise ValueError("GitHub Check Runs provider response is incomplete")
        count = payload["total_count"]
        batch = payload["check_runs"]
        if expected_count is None:
            expected_count = count
        elif count != expected_count:
            raise ValueError("GitHub Check Runs listing changed during pagination")
        if count < 0 or count > MAX_CHECK_ROWS or len(batch) > 100:
            raise ValueError("GitHub Check Runs exceed bounded complete query")
        if not all(isinstance(row, dict) for row in batch):
            raise ValueError("malformed provider Check Run")
        rows.extend(batch)
        identifiers = [row.get("id") for row in rows]
        if any(
            type(identifier) is not int or identifier <= 0 for identifier in identifiers
        ) or len(set(identifiers)) != len(identifiers):
            raise ValueError(
                "GitHub provider Check Run IDs are incomplete or duplicate"
            )
        if len(rows) == count:
            return rows
        if len(rows) > count or not batch or page >= 20:
            raise ValueError("GitHub Check Runs listing is truncated or inconsistent")
        page += 1


def _select_check(
    rows: list[dict[str, Any]], *, sha: str, check_name: str
) -> dict[str, Any] | None:
    selected: list[dict[str, Any]] = []
    for row in rows:
        if row.get("name") != check_name:
            continue
        app = row.get("app")
        if not isinstance(app, dict) or app.get("slug") != "github-actions":
            continue
        if (
            row.get("head_sha") != sha
            or type(row.get("id")) is not int
            or row["id"] <= 0
            or row.get("status")
            not in {
                "queued",
                "in_progress",
                "completed",
                "pending",
                "requested",
                "waiting",
            }
        ):
            raise ValueError("GitHub Check Run contradicts its exact identity")
        selected.append(row)
    if not selected:
        return None
    # A rerun creates a later Check Run. Never use an older success when a
    # newer attempt is pending or has failed. Duplicate IDs are ambiguous.
    if len({row["id"] for row in selected}) != len(selected):
        raise ValueError("duplicate provider Check Run IDs")
    last = max(selected, key=lambda row: row["id"])
    if last["status"] == "completed" and last.get("conclusion") == "success":
        # A trusted check receipt needs temporal and URL provenance as well
        # as the provider's status; absent/malformed metadata is UNKNOWN.
        when = last.get("completed_at")
        url = last.get("details_url")
        if not isinstance(when, str) or not isinstance(url, str):
            raise ValueError("successful Check Run lacks temporal or URL provenance")
        try:
            instant = datetime.fromisoformat(when)
        except ValueError as exc:
            raise ValueError(
                "successful Check Run has invalid completion time"
            ) from exc
        parsed = urlsplit(url)
        if (
            instant.tzinfo is None
            or parsed.scheme != "https"
            or parsed.hostname != "github.com"
            or not parsed.path.startswith("/ordivon-org/ordivon/actions/")
        ):
            raise ValueError("successful Check Run has unqualified provenance")
    return {
        "checkRunId": last["id"],
        "checkName": check_name,
        "headSha": sha,
        "app": "github-actions",
        "status": last["status"],
        "conclusion": last.get("conclusion"),
        "completedAt": last.get("completed_at"),
        "detailsUrl": last.get("details_url"),
    }

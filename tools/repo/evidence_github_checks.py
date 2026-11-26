"""Bounded read-only GitHub Check Run observation and native attempt identity."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any
from urllib.parse import urlsplit

from ci_telemetry import Gh
from github_workflow_observation import complete_page_geometry

MAX_CHECK_ROWS = 2000
MAX_REFERENCE_SUITES = 1000


class CheckObservationError(ValueError):
    """Typed unresolved provider obligation, not a negative check result."""

    def __init__(
        self, reason: str, detail: str, *, contexts: list[dict[str, Any]] | None = None
    ):
        super().__init__(detail)
        self.reason = reason
        self.contexts = contexts or []


def bounded_provider_rows(
    gh: Gh, endpoint: str, *, key: str, label: str, max_rows: int = MAX_CHECK_ROWS
) -> list[dict[str, Any]]:
    """Validate bounded native pagination; not an atomic provider snapshot."""
    rows: list[dict[str, Any]] = []
    expected_count = None
    separator = "&" if "?" in endpoint else "?"
    for page in range(1, (max_rows + 99) // 100 + 1):
        payload = gh.api(f"{endpoint}{separator}per_page=100&page={page}")
        if (
            not isinstance(payload, dict)
            or type(payload.get("total_count")) is not int
            or not isinstance(payload.get(key), list)
        ):
            raise ValueError(f"{label} provider response is incomplete")
        count = payload["total_count"]
        batch = payload[key]
        if expected_count is None:
            expected_count = count
        elif count != expected_count:
            raise ValueError(f"{label} listing changed during pagination")
        if not 0 <= count <= max_rows:
            raise ValueError(f"{label} exceeds bounded complete query")
        if not complete_page_geometry(count, len(rows), len(batch)):
            raise ValueError(f"{label} page geometry is truncated or inconsistent")
        if not all(isinstance(row, dict) for row in batch):
            raise ValueError(f"malformed provider {label} row")
        rows.extend(batch)
        identifiers = [row.get("id") for row in rows]
        if any(type(identifier) is not int or identifier <= 0 for identifier in identifiers):
            raise ValueError(f"{label} provider IDs are incomplete")
        if len(set(identifiers)) != len(identifiers):
            raise ValueError(f"{label} provider IDs are duplicate")
        if len(rows) == count:
            return rows
        if len(rows) > count or not batch:
            break
    raise ValueError(f"{label} listing is truncated or inconsistent")


def _check_suite_count(gh: Gh, repo: str, sha: str) -> tuple[int, int | None]:
    # GitHub's commit Check Runs endpoint observes at most 1000 suites.
    # A small returned Check Run count is not evidence the suite cap was not hit.
    payload = gh.api(f"repos/{repo}/commits/{sha}/check-suites?per_page=1")
    if not isinstance(payload, dict) or type(payload.get("total_count")) is not int:
        raise CheckObservationError("UNKNOWN_CHECK_SUITE_COVERAGE", "missing Check Suite count")
    count = payload["total_count"]
    rows = payload.get("check_suites")
    if count < 0 or not isinstance(rows, list) or len(rows) != min(count, 1):
        raise CheckObservationError("UNKNOWN_CHECK_SUITE_COVERAGE", "invalid Check Suite listing")
    if count > MAX_REFERENCE_SUITES:
        raise CheckObservationError(
            "UNKNOWN_CHECK_SUITE_COVERAGE",
            "Git reference exceeds native Check Run endpoint suite coverage; enumerate suites explicitly",
        )
    first = rows[0] if rows else None
    if first is not None and (
        not isinstance(first, dict)
        or type(first.get("id")) is not int or first["id"] <= 0
        or first.get("head_sha") != sha
    ):
        raise CheckObservationError("UNKNOWN_CHECK_SUITE_COVERAGE", "unqualified Check Suite identity")
    return count, first["id"] if first else None


def _provider_checks(gh: Gh, repo: str, sha: str) -> list[dict[str, Any]]:
    """Read bounded all-attempts listing and qualify native suite coverage."""
    before = _check_suite_count(gh, repo, sha)
    rows = bounded_provider_rows(
        gh, f"repos/{repo}/commits/{sha}/check-runs?filter=all",
        key="check_runs", label="GitHub Check Runs",
    )
    if (rows and before[0] == 0) or _check_suite_count(gh, repo, sha) != before:
        raise CheckObservationError("UNKNOWN_CHECK_SUITE_COVERAGE", "Check Suite listing changed")
    return rows


def _context(row: dict[str, Any], repo: str) -> tuple[int, int]:
    suite = row.get("check_suite")
    url = row.get("details_url")
    if not isinstance(suite, dict) or type(suite.get("id")) is not int or suite["id"] <= 0:
        raise CheckObservationError("UNKNOWN_WORKFLOW_CONTEXT", "missing native Check Suite identity")
    if not isinstance(url, str):
        raise CheckObservationError("UNKNOWN_WORKFLOW_CONTEXT", "missing native Check Run details URL")
    parsed = urlsplit(url)
    match = re.fullmatch(
        "/" + re.escape(repo) + r"/actions/runs/([1-9][0-9]*)/job/([1-9][0-9]*)",
        parsed.path,
    )
    if (
        parsed.scheme != "https" or parsed.netloc != "github.com"
        or parsed.query or parsed.fragment or match is None
        or int(match.group(2)) != row["id"]
    ):
        raise CheckObservationError("UNKNOWN_WORKFLOW_CONTEXT", "unqualified native Check Run URL provenance")
    return suite["id"], int(match.group(1))


def _native_attempt_selection(
    gh: Gh, repo: str, sha: str, check_name: str, selected: list[dict[str, Any]]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Join Check Run, Workflow Run and latest native Attempt Job identity."""
    contexts = {_context(row, repo) for row in selected}
    if len(contexts) != 1:
        # These are observed provider identities, not selected/latest attempts.
        choices = [
            {
                "checkSuiteId": suite_id, "workflowRunId": run_id,
                "observedCheckRunIds": sorted(
                    row["id"] for row in selected if _context(row, repo) == (suite_id, run_id)
                ),
            }
            for suite_id, run_id in sorted(contexts)
        ]
        raise CheckObservationError(
            "UNKNOWN_AMBIGUOUS_WORKFLOW_CONTEXT",
            "same named Check Runs belong to distinct workflow contexts; explicit context required",
            contexts=choices,
        )
    suite_id, run_id = next(iter(contexts))
    endpoint = f"repos/{repo}/actions/runs/{run_id}"

    def run_identity() -> tuple[Any, ...]:
        run = gh.api(endpoint)
        if (
            not isinstance(run, dict) or run.get("id") != run_id
            or run.get("head_sha") != sha or run.get("check_suite_id") != suite_id
            or not isinstance(run.get("repository"), dict)
            or run["repository"].get("full_name") != repo
            or type(run.get("run_attempt")) is not int or run["run_attempt"] < 1
            or not isinstance(run.get("path"), str)
            or not run["path"].startswith(".github/workflows/")
            or (check_name == "root-verification" and run["path"] != ".github/workflows/ci.yml")
        ):
            raise CheckObservationError("UNKNOWN_WORKFLOW_CONTEXT", "native workflow run identity mismatch")
        return (
            run["run_attempt"], run["path"], run.get("event"),
            run.get("status"), run.get("conclusion"),
        )

    before = run_identity()
    attempt = before[0]
    jobs = bounded_provider_rows(
        gh, f"{endpoint}/attempts/{attempt}/jobs",
        key="jobs", label="GitHub Attempt Jobs",
    )
    matches = [job for job in jobs if job.get("name") == check_name]
    if len(matches) != 1:
        raise CheckObservationError(
            "UNKNOWN_WORKFLOW_ATTEMPT_CHECK",
            "current native workflow attempt lacks one unique named job",
        )
    job = matches[0]
    candidates = [row for row in selected if row["id"] == job["id"]]
    expected_url = f"https://api.github.com/repos/{repo}/check-runs/{job['id']}"
    if (
        len(candidates) != 1 or job.get("run_id") != run_id
        or job.get("run_attempt") != attempt or job.get("head_sha") != sha
        or job.get("check_run_url") != expected_url
        or job.get("status") != candidates[0]["status"]
        or job.get("conclusion") != candidates[0].get("conclusion")
    ):
        raise CheckObservationError(
            "UNKNOWN_WORKFLOW_ATTEMPT_CHECK",
            "native attempt job and Check Run identity or observed status disagree",
        )
    if run_identity() != before:
        raise CheckObservationError("UNKNOWN_WORKFLOW_ATTEMPT_CHECK", "workflow attempt changed during observation")
    return candidates[0], {
        "checkSuiteId": suite_id,
        "workflowRunId": run_id,
        "workflowRunAttempt": attempt,
        "workflowPath": before[1],
        "workflowEvent": before[2],
        "selectionBasis": "NATIVE_WORKFLOW_RUN_ATTEMPT_JOB",
        "observationAtomic": False,
    }


def _select_check(
    rows: list[dict[str, Any]], *, sha: str, check_name: str, gh: Gh, repo: str,
    workflow_run_id: int | None = None,
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
            or type(row.get("id")) is not int or row["id"] <= 0
            or row.get("status") not in {
                "queued", "in_progress", "completed", "pending", "requested", "waiting",
            }
        ):
            raise ValueError("GitHub Check Run contradicts its exact identity")
        selected.append(row)
    if workflow_run_id is not None:
        if type(workflow_run_id) is not int or workflow_run_id <= 0:
            raise ValueError("workflow run identity must be a positive integer")
        selected = [row for row in selected if _context(row, repo)[1] == workflow_run_id]
        if not selected:
            raise CheckObservationError(
                "UNKNOWN_REQUESTED_WORKFLOW_CONTEXT",
                "requested Workflow Run has no observed named check at the exact SourceCut",
            )
    if not selected:
        return None
    if len({row["id"] for row in selected}) != len(selected):
        raise ValueError("duplicate provider Check Run IDs")
    # Native run/attempt identity selects the job; numeric IDs never define order.
    last, context = _native_attempt_selection(gh, repo, sha, check_name, selected)
    if last["status"] == "completed" and last.get("conclusion") == "success":
        when = last.get("completed_at")
        url = last.get("details_url")
        if not isinstance(when, str) or not isinstance(url, str):
            raise ValueError("successful Check Run lacks temporal or URL provenance")
        try:
            instant = datetime.fromisoformat(when)
        except ValueError as exc:
            raise ValueError("successful Check Run has invalid completion time") from exc
        parsed = urlsplit(url)
        if (
            instant.tzinfo is None or parsed.scheme != "https"
            or parsed.hostname != "github.com"
            or not parsed.path.startswith("/" + repo + "/actions/")
        ):
            raise ValueError("successful Check Run has unqualified provenance")
    return {
        "checkRunId": last["id"], "checkName": check_name,
        "headSha": sha, "app": "github-actions",
        "status": last["status"], "conclusion": last.get("conclusion"),
        "completedAt": last.get("completed_at"), "detailsUrl": last.get("details_url"),
        **context,
    }

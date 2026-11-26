"""Observed named Owner-shard intervals, never task-level or causal costs."""
from __future__ import annotations

import re
from typing import Any

from github_workflow_observation import instant, seconds, summary

WORKFLOW_PATH = ".github/workflows/ci.yml"
ANCHORS = (
    "Setup root verification",
    "Preinstall selected Owner tools with native mise",
    "Verify affected owners",
)
PHASE_FIELDS = (
    "beforeVerifySeconds", "verifyStepSeconds", "afterVerifySeconds",
    "rootSetupSeconds", "ownerToolInstallSeconds",
)


def _completed(row: dict[str, Any]) -> bool:
    conclusion = row.get("conclusion")
    return (
        row.get("status") == "completed"
        and isinstance(conclusion, str)
        and bool(conclusion)
        and conclusion != "skipped"
    )


def _phase_intervals(job: dict[str, Any]) -> dict[str, float] | None:
    start, end = instant(job.get("startedAt")), instant(job.get("completedAt"))
    if not _completed(job) or start is None or end is None or start > end:
        return None
    intervals = []
    for name in ANCHORS:
        matches = [step for step in job["steps"] if step.get("name") == name]
        if len(matches) != 1:
            return None
        step = matches[0]
        a, b = instant(step.get("startedAt")), instant(step.get("completedAt"))
        n = step.get("number")
        if (
            not _completed(step) or type(n) is not int or n < 1
            or a is None or b is None or not start <= a <= b <= end
        ):
            return None
        intervals.append((n, a, b))
    setup, install, verify = intervals
    if not (
        setup[0] < install[0] < verify[0]
        and setup[2] <= install[1] and install[2] <= verify[1]
    ):
        return None
    return {
        "beforeVerifySeconds": (verify[1] - start).total_seconds(),
        "verifyStepSeconds": (verify[2] - verify[1]).total_seconds(),
        "afterVerifySeconds": (end - verify[2]).total_seconds(),
        "rootSetupSeconds": (setup[2] - setup[1]).total_seconds(),
        "ownerToolInstallSeconds": (install[2] - install[1]).total_seconds(),
    }


def observe_owner_shard_phases(runs: list[dict[str, Any]]) -> dict[str, Any]:
    """Partition job envelopes using unique native steps in the named workflow.

    This is descriptive: verify includes guards and task setup; setup/install
    are subsets of beforeVerify, and created-to-start is not a causal wait
    attribution. Unknown anchors exclude the entire partition from summaries.
    """
    rows = []
    for run in runs:
        if run.get("workflowPath") != WORKFLOW_PATH:
            continue
        for job in run["jobs"]:
            if not re.fullmatch(r"owner-shard-(0|[1-9][0-9]*)", job.get("name") or ""):
                continue
            phases = _phase_intervals(job)
            rows.append({
                "runId": run["runId"], "runAttempt": run["runAttempt"],
                "headSha": run.get("headSha"), "jobId": job["jobId"],
                "jobName": job["name"], "conclusion": job.get("conclusion"),
                "standing": "QUALIFIED_NAMED_INTERVALS" if phases is not None else "UNKNOWN",
                "runnerWaitSeconds": seconds(job.get("createdAt"), job.get("startedAt")),
                "jobSeconds": seconds(job.get("startedAt"), job.get("completedAt")) if _completed(job) else None,
                **(phases if phases is not None else dict.fromkeys(PHASE_FIELDS)),
            })
    rows.sort(key=lambda row: (row["runId"], row["runAttempt"], row["jobId"]))
    return {
        "scope": "NAMED_NATIVE_JOB_STEP_INTERVALS_NOT_TASK_OR_BILLING_COST",
        "observedJobs": len(rows),
        "qualifiedJobs": sum(row["standing"] == "QUALIFIED_NAMED_INTERVALS" for row in rows),
        "rows": rows,
        "summary": {field: summary(row[field] for row in rows)
                    for field in ("runnerWaitSeconds", "jobSeconds", *PHASE_FIELDS)},
    }

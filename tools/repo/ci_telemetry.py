#!/usr/bin/env python3
"""Read-only GitHub Actions observation projection for convergence economics.

This module observes workflow runs/jobs/steps. It does not cancel runs, reuse
evidence, schedule work, or decide whether a provider action should change.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from statistics import mean, median
from typing import Any, Iterable

ECONOMIC_OUTCOMES = {
    "UNCLASSIFIED",
    "USEFUL",
    "SAVED_WORK",
    "AVOIDABLE_WASTE",
    "FAILED_PRODUCTIVELY",
    "INFRA_FAILURE",
    "DUPLICATED",
    "SUPERSEDED",
    "NO_EXECUTION",
    "PENDING",
}


def instant(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def seconds(start: str | None, end: str | None) -> float | None:
    a, b = instant(start), instant(end)
    if a is None or b is None:
        return None
    return max(0.0, (b - a).total_seconds())


def summary(values: Iterable[float | None]) -> dict[str, float | int | None]:
    xs = sorted(float(x) for x in values if x is not None)
    if not xs:
        return {"count": 0, "mean": None, "median": None, "p95": None, "max": None}
    rank = max(0, min(len(xs) - 1, int((0.95 * len(xs) + 0.999999999) // 1) - 1))
    return {
        "count": len(xs),
        "mean": round(mean(xs), 3),
        "median": round(median(xs), 3),
        "p95": round(xs[rank], 3),
        "max": round(max(xs), 3),
    }


@dataclass(frozen=True)
class ProviderSnapshot:
    repository: str
    runs: list[dict[str, Any]]
    jobs: dict[str, list[dict[str, Any]]]


class Gh:
    def __init__(self, repo: str):
        self.repo = repo

    def api(self, endpoint: str) -> Any:
        cmd = ["gh", "api", "-H", "Accept: application/vnd.github+json", endpoint]
        out = subprocess.run(cmd, check=True, text=True, capture_output=True).stdout
        return json.loads(out)

    def collect(
        self,
        *,
        limit: int,
        events: tuple[str, ...],
        workflow_name: str | None,
    ) -> ProviderSnapshot:
        owner, repo = self.repo.split("/", 1)
        runs_by_id: dict[int, dict[str, Any]] = {}
        per_page = min(max(limit, 1), 100)
        for event in events:
            payload = self.api(
                f"repos/{owner}/{repo}/actions/runs?event={event}&per_page={per_page}"
            )
            rows = payload.get("workflow_runs", [])
            if workflow_name:
                rows = [row for row in rows if row.get("name") == workflow_name]
            for row in rows[:limit]:
                runs_by_id[int(row["id"])] = row

        runs = sorted(
            runs_by_id.values(),
            key=lambda row: (row.get("created_at") or "", int(row["id"])),
        )
        jobs: dict[str, list[dict[str, Any]]] = {}
        for run in runs:
            run_id = str(run["id"])
            jobs[run_id] = self.api(
                f"repos/{owner}/{repo}/actions/runs/{run_id}/jobs?per_page=100"
            ).get("jobs", [])
        return ProviderSnapshot(self.repo, runs, jobs)


def termination_reason(run: dict[str, Any]) -> str:
    if run.get("status") != "completed":
        return "IN_PROGRESS"
    conclusion = (run.get("conclusion") or "UNKNOWN").upper()
    return conclusion


def default_economic_outcome(run: dict[str, Any], jobs: list[dict[str, Any]]) -> str:
    if run.get("status") != "completed":
        return "PENDING"
    if (run.get("conclusion") or "").lower() == "skipped" and not jobs:
        return "NO_EXECUTION"
    # A provider conclusion is not enough to call compute useful or waste.
    return "UNCLASSIFIED"


def _normalize_step(step: dict[str, Any]) -> dict[str, Any]:
    return {
        "number": step.get("number"),
        "name": step.get("name"),
        "status": step.get("status"),
        "conclusion": step.get("conclusion"),
        "startedAt": step.get("started_at"),
        "completedAt": step.get("completed_at"),
        "durationSeconds": seconds(step.get("started_at"), step.get("completed_at")),
    }


def _normalize_job(job: dict[str, Any]) -> dict[str, Any]:
    return {
        "jobId": job.get("id"),
        "name": job.get("name"),
        "status": job.get("status"),
        "conclusion": job.get("conclusion"),
        "createdAt": job.get("created_at"),
        "startedAt": job.get("started_at"),
        "completedAt": job.get("completed_at"),
        "runnerWaitSeconds": seconds(job.get("created_at"), job.get("started_at")),
        "executionSeconds": seconds(job.get("started_at"), job.get("completed_at")),
        "steps": [_normalize_step(step) for step in job.get("steps", [])],
    }


def normalize(
    snapshot: ProviderSnapshot,
    *,
    economic_annotations: dict[str, dict[str, str]] | None = None,
) -> dict[str, Any]:
    annotations = economic_annotations or {}
    normalized_runs: list[dict[str, Any]] = []
    for run in snapshot.runs:
        run_id = str(run["id"])
        jobs = snapshot.jobs.get(run_id, [])
        annotation = annotations.get(run_id)
        economic = default_economic_outcome(run, jobs)
        economic_reason = "provider conclusion alone is insufficient for economic classification"
        if annotation:
            candidate = annotation.get("economicOutcome", "")
            if candidate not in ECONOMIC_OUTCOMES:
                raise ValueError(f"unsupported economic outcome for run {run_id}: {candidate}")
            economic = candidate
            economic_reason = annotation.get("reason", "explicit evidence annotation")

        normalized_jobs = [_normalize_job(job) for job in jobs]
        normalized_runs.append(
            {
                "schemaVersion": 1,
                "kind": "ordivon.ci-run-observation",
                "provider": "github",
                "repository": snapshot.repository,
                "runId": run.get("id"),
                "workflowId": run.get("workflow_id"),
                "workflowName": run.get("name"),
                "event": run.get("event"),
                "headSha": run.get("head_sha"),
                "headBranch": run.get("head_branch"),
                "runAttempt": run.get("run_attempt"),
                "status": run.get("status"),
                "conclusion": run.get("conclusion"),
                "createdAt": run.get("created_at"),
                "startedAt": run.get("run_started_at"),
                "updatedAt": run.get("updated_at"),
                "wallSeconds": seconds(run.get("created_at"), run.get("updated_at")),
                "terminationReason": termination_reason(run),
                "economicOutcome": economic,
                "economicReason": economic_reason,
                "jobs": normalized_jobs,
            }
        )
    return {
        "schemaVersion": 1,
        "kind": "ordivon.ci-observation-set",
        "provider": "github",
        "repository": snapshot.repository,
        "runs": sorted(normalized_runs, key=lambda row: (row["createdAt"] or "", row["runId"])),
    }


def extract_metrics(normalized: dict[str, Any]) -> dict[str, Any]:
    runs = normalized["runs"]
    root_jobs = [
        job
        for run in runs
        for job in run["jobs"]
        if job.get("name") == "root-verification"
    ]
    steps_by_name: dict[str, list[float | None]] = defaultdict(list)
    for run in runs:
        for job in run["jobs"]:
            for step in job["steps"]:
                steps_by_name[step.get("name") or "<unnamed>"].append(
                    step.get("durationSeconds")
                )

    outcome_counts = Counter(run["economicOutcome"] for run in runs)
    termination_counts = Counter(run["terminationReason"] for run in runs)
    avoidable_runs = [
        run
        for run in runs
        if run["economicOutcome"] in {"AVOIDABLE_WASTE", "DUPLICATED"}
    ]
    avoidable_seconds = sum(
        float(job["executionSeconds"])
        for run in avoidable_runs
        for job in run["jobs"]
        if job.get("executionSeconds") is not None
    )
    return {
        "runs": len(runs),
        "eventCounts": dict(sorted(Counter(run.get("event") or "unknown" for run in runs).items())),
        "terminationReasonCounts": dict(sorted(termination_counts.items())),
        "economicOutcomeCounts": dict(sorted(outcome_counts.items())),
        "unclassifiedTerminalRuns": sum(
            1
            for run in runs
            if run["status"] == "completed" and run["economicOutcome"] == "UNCLASSIFIED"
        ),
        "explicitAvoidableWasteRuns": len(avoidable_runs),
        "explicitAvoidableWasteExecutionSeconds": round(avoidable_seconds, 3),
        "rootVerificationExecutionSeconds": summary(
            job.get("executionSeconds") for job in root_jobs
        ),
        "rootVerificationRunnerWaitSeconds": summary(
            job.get("runnerWaitSeconds") for job in root_jobs
        ),
        "stepSecondsByName": {
            name: summary(values) for name, values in sorted(steps_by_name.items())
        },
    }


def project(normalized: dict[str, Any]) -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "kind": "ordivon.ci-observation-projection",
        "authority": {
            "runs": "GitHub Actions",
            "projection": "tools/repo/ci_telemetry.py",
            "durableLocalRunState": False,
            "diagnosisAuthority": False,
            "controlAuthority": False,
        },
        "coverage": {
            "repository": normalized["repository"],
            "runs": len(normalized["runs"]),
        },
        "runs": normalized["runs"],
        "metrics": extract_metrics(normalized),
    }


def snapshot_from_json(data: dict[str, Any]) -> ProviderSnapshot:
    return ProviderSnapshot(
        repository=data["repository"],
        runs=data["runs"],
        jobs=data["jobs"],
    )


def snapshot_to_json(snapshot: ProviderSnapshot) -> dict[str, Any]:
    return {
        "repository": snapshot.repository,
        "runs": snapshot.runs,
        "jobs": snapshot.jobs,
    }


def _annotations(path: Path | None) -> dict[str, dict[str, str]]:
    if path is None:
        return {}
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError("economic annotations must be a JSON object keyed by run id")
    return {str(key): row for key, row in value.items()}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default="ordivon-org/ordivon")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument(
        "--events",
        default="pull_request,merge_group,push",
        help="comma-separated GitHub Actions event names",
    )
    parser.add_argument("--workflow-name", default="Monorepo Required")
    parser.add_argument("--input", type=Path, help="analyze a saved provider snapshot")
    parser.add_argument("--snapshot-output", type=Path)
    parser.add_argument("--normalized-output", type=Path)
    parser.add_argument("--economic-annotations", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    if args.input:
        snapshot = snapshot_from_json(json.loads(args.input.read_text()))
    else:
        events = tuple(item.strip() for item in args.events.split(",") if item.strip())
        snapshot = Gh(args.repo).collect(
            limit=args.limit,
            events=events,
            workflow_name=args.workflow_name or None,
        )
    if args.snapshot_output:
        args.snapshot_output.write_text(
            json.dumps(snapshot_to_json(snapshot), indent=2) + "\n"
        )
    normalized = normalize(
        snapshot, economic_annotations=_annotations(args.economic_annotations)
    )
    if args.normalized_output:
        args.normalized_output.write_text(json.dumps(normalized, indent=2) + "\n")
    rendered = json.dumps(project(normalized), indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered)
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

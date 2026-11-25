#!/usr/bin/env python3
"""Read-only GitHub Actions observation projection for convergence economics.

This module observes workflow runs/jobs/steps. It does not cancel runs, reuse
evidence, schedule work, or decide whether a provider action should change.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from github_workflow_observation import (
    GitHubWorkflowReader, instant, run_identity, seconds, summary, validate_attempt_jobs,
)

from ci_economic_annotation import ECONOMIC_OUTCOMES, bind_annotation


@dataclass(frozen=True)
class ProviderSnapshot:
    repository: str
    runs: list[dict[str, Any]]
    jobs: dict[str, list[dict[str, Any]]]


class Gh(GitHubWorkflowReader):
    def collect(
        self,
        *,
        limit: int,
        events: tuple[str, ...],
        workflow_name: str | None,
    ) -> ProviderSnapshot:
        if limit < 1:
            raise ValueError("CI observation limit must be positive")
        owner, repo = self.repo.split("/", 1)
        runs_by_id: dict[int, dict[str, Any]] = {}
        per_page = min(limit, 100)
        for event in events:
            matched = 0
            page = 1
            while matched < limit:
                payload = self.api(
                    f"repos/{owner}/{repo}/actions/runs?event={event}&per_page={per_page}&page={page}"
                )
                rows = payload.get("workflow_runs", [])
                for row in rows:
                    if workflow_name and row.get("name") != workflow_name:
                        continue
                    run_id, _ = run_identity(row)
                    if run_id in runs_by_id:
                        raise ValueError("duplicate sampled workflow run")
                    runs_by_id[run_id] = row
                    matched += 1
                    if matched == limit:
                        break
                if len(rows) < per_page:
                    break
                page += 1

        runs = sorted(
            runs_by_id.values(),
            key=lambda row: (row.get("created_at") or "", int(row["id"])),
        )
        jobs = {}
        for run in runs:
            run_id, attempt = run_identity(run)
            jobs[str(run_id)] = self.collect_attempt_jobs(run_id, attempt)
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
        "runId": job.get("run_id"),
        "runAttempt": job.get("run_attempt"),
        "name": job.get("name"),
        "status": job.get("status"),
        "conclusion": job.get("conclusion"),
        "createdAt": job.get("created_at"),
        "startedAt": job.get("started_at"),
        "completedAt": job.get("completed_at"),
        "runnerWaitSeconds": seconds(job.get("created_at"), job.get("started_at")),
        "executionSeconds": (
            seconds(job.get("started_at"), job.get("completed_at"))
            if job.get("status") == "completed" and job.get("conclusion") != "skipped"
            else None
        ),
        "steps": [_normalize_step(step) for step in job.get("steps", [])],
    }


def qualified_economic_annotation(
    run: dict[str, Any], annotation: dict[str, Any]
) -> tuple[str, str]:
    native_id, attempt = run_identity(run)
    qualified = bind_annotation(annotation, {
        "runId": native_id, "attempt": attempt, "headSha": run.get("head_sha"),
        "event": run.get("event"), "providerConclusion": run.get("conclusion"),
    }, status=run.get("status"))
    return qualified["economicOutcome"], qualified["reason"]


def normalize(
    snapshot: ProviderSnapshot,
    *,
    economic_annotations: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    annotations = economic_annotations or {}
    normalized_runs: list[dict[str, Any]] = []
    run_ids = [str(run_identity(run)[0]) for run in snapshot.runs]
    if len(run_ids) != len(set(run_ids)) or set(run_ids) != set(snapshot.jobs):
        raise ValueError("workflow snapshot has duplicate runs or missing/extra job lists")
    seen_jobs: set[int] = set()
    for run in snapshot.runs:
        native_id, attempt = run_identity(run)
        run_id = str(native_id)
        jobs = snapshot.jobs[run_id]
        if not isinstance(jobs, list):
            raise ValueError("malformed workflow snapshot job list")
        validate_attempt_jobs(jobs, native_id, attempt, seen_jobs)
        annotation = annotations.get(run_id)
        economic = default_economic_outcome(run, jobs)
        economic_reason = "provider conclusion alone is insufficient for economic classification"
        if run_id in annotations:
            economic, economic_reason = qualified_economic_annotation(run, annotation)

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
                **({"economicAnnotation": {**annotation, "evidenceRefs": list(annotation["evidenceRefs"])}}
                   if run_id in annotations else {}),
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


def observed_attempt_execution(run: dict[str, Any]) -> float | None:
    """Sum measured job execution, not elapsed wall time or billed CPU time."""
    if run.get("status") != "completed":
        return None
    jobs = [job for job in run["jobs"] if job.get("conclusion") != "skipped"]
    if not jobs or any(job.get("executionSeconds") is None for job in jobs):
        return None
    return sum(job["executionSeconds"] for job in jobs)


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
        "observedAttemptJobExecutionSeconds": summary(
            observed_attempt_execution(run) for run in runs
        ),
        "jobsWithoutMeasuredExecutionSeconds": sum(
            job.get("executionSeconds") is None for run in runs for job in run["jobs"]
        ),
        "skippedJobs": sum(
            job.get("conclusion") == "skipped" for run in runs for job in run["jobs"]
        ),
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
            "attemptScope": "OBSERVED_ATTEMPT_ONLY",
            "historyCoverage": "BOUNDED_NONATOMIC_PROVIDER_SAMPLE",
            "jobCostScope": "SUM_OF_OBSERVED_JOB_DURATIONS_NOT_BILLED_CPU_OR_WALL_TIME",
            "rootVerificationScope": "NAMED_JOB_ONLY_NOT_ALL_WORKFLOW_JOBS",
            "wallTimeScope": "RUN_CREATED_TO_UPDATED_NOT_ATTEMPT_CPU_TIME",
            "snapshotReplayScope": "SUPPLIED_JOB_ROWS_NOT_PROVIDER_COMPLETENESS_PROOF",
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


def _annotations(path: Path | None) -> dict[str, dict[str, Any]]:
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

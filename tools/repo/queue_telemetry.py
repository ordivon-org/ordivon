#!/usr/bin/env python3
"""Read-only GitHub Merge Queue observation projection.

GitHub remains queue/run authority. This module may collect provider data and
normalize it, but it owns no durable queue state, diagnosis policy, scheduler,
or control loop.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from statistics import mean, median
from typing import Any, Iterable

PR_FROM_QUEUE_BRANCH = re.compile(r"(?:^|/)pr-(\d+)-")


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
    pulls: list[dict[str, Any]]
    timelines: dict[str, list[dict[str, Any]]]
    merge_group_runs: list[dict[str, Any]]
    jobs: dict[str, list[dict[str, Any]]]


class Gh:
    def __init__(self, repo: str):
        self.repo = repo

    def api(self, endpoint: str) -> Any:
        cmd = ["gh", "api", "-H", "Accept: application/vnd.github+json", endpoint]
        out = subprocess.run(cmd, check=True, text=True, capture_output=True).stdout
        return json.loads(out)

    def paginated_list(self, endpoint: str) -> list[dict[str, Any]]:
        cmd = [
            "gh",
            "api",
            "-H",
            "Accept: application/vnd.github+json",
            "--paginate",
            "--slurp",
            endpoint,
        ]
        pages = json.loads(
            subprocess.run(cmd, check=True, text=True, capture_output=True).stdout
        )
        return [item for page in pages for item in page]

    def collect(self, limit: int) -> ProviderSnapshot:
        owner, repo = self.repo.split("/", 1)
        pulls = self.api(
            f"repos/{owner}/{repo}/pulls?state=closed&sort=updated&direction=desc&per_page={limit}"
        )
        merged = [p for p in pulls if p.get("merged_at")]
        timelines: dict[str, list[dict[str, Any]]] = {}
        for pr in merged:
            number = str(pr["number"])
            timelines[number] = self.paginated_list(
                f"repos/{owner}/{repo}/issues/{number}/timeline?per_page=100"
            )

        runs_payload = self.api(
            f"repos/{owner}/{repo}/actions/runs?event=merge_group&per_page=100"
        )
        runs = runs_payload.get("workflow_runs", [])
        jobs: dict[str, list[dict[str, Any]]] = {}
        for run in runs:
            run_id = str(run["id"])
            jobs[run_id] = self.api(
                f"repos/{owner}/{repo}/actions/runs/{run_id}/jobs?per_page=100"
            ).get("jobs", [])
        return ProviderSnapshot(self.repo, merged, timelines, runs, jobs)


def _run_pr(run: dict[str, Any]) -> int | None:
    match = PR_FROM_QUEUE_BRANCH.search(run.get("head_branch") or "")
    return int(match.group(1)) if match else None


def _required_job(jobs: list[dict[str, Any]]) -> dict[str, Any] | None:
    return next((job for job in jobs if job.get("name") == "root-verification"), None)


def normalize(snapshot: ProviderSnapshot) -> dict[str, Any]:
    """Translate provider-shaped fields into canonical queue episodes.

    This is the provider boundary. Diagnosis and control are intentionally absent.
    """
    runs_by_pr: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for run in snapshot.merge_group_runs:
        pr = _run_pr(run)
        if pr is not None:
            runs_by_pr[pr].append(run)

    episodes: list[dict[str, Any]] = []
    transitions: list[dict[str, Any]] = []
    for pr in snapshot.pulls:
        number = int(pr["number"])
        timeline = snapshot.timelines.get(str(number), [])
        enqueues = sorted(
            event["created_at"]
            for event in timeline
            if event.get("event") == "added_to_merge_queue" and event.get("created_at")
        )
        removals = sorted(
            event["created_at"]
            for event in timeline
            if event.get("event") == "removed_from_merge_queue" and event.get("created_at")
        )
        transitions.extend(
            {"pr": number, "at": value, "delta": 1, "event": "ENQUEUED"}
            for value in enqueues
        )
        transitions.extend(
            {"pr": number, "at": value, "delta": -1, "event": "DEQUEUED"}
            for value in removals
        )

        normalized_runs: list[dict[str, Any]] = []
        for run in sorted(runs_by_pr.get(number, []), key=lambda row: row.get("created_at") or ""):
            jobs = snapshot.jobs.get(str(run["id"]), [])
            required = _required_job(jobs)
            normalized_runs.append(
                {
                    "runId": run.get("id"),
                    "sha": run.get("head_sha"),
                    "createdAt": run.get("created_at"),
                    "status": run.get("status"),
                    "conclusion": run.get("conclusion"),
                    "requiredVerification": None
                    if required is None
                    else {
                        "jobId": required.get("id"),
                        "createdAt": required.get("created_at"),
                        "startedAt": required.get("started_at"),
                        "completedAt": required.get("completed_at"),
                        "status": required.get("status"),
                        "conclusion": required.get("conclusion"),
                    },
                }
            )

        head = pr.get("head") or {}
        episodes.append(
            {
                "schemaVersion": 1,
                "kind": "ordivon.queue-episode",
                "provider": "github",
                "repository": snapshot.repository,
                "pr": number,
                "prHeadSha": head.get("sha"),
                "enqueueTimes": enqueues,
                "removalTimes": removals,
                "mergedAt": pr.get("merged_at"),
                "mergeGroupRuns": normalized_runs,
            }
        )

    return {
        "schemaVersion": 1,
        "kind": "ordivon.queue-observation-set",
        "provider": "github",
        "repository": snapshot.repository,
        "episodes": sorted(episodes, key=lambda row: row["pr"]),
        "queueTransitions": sorted(
            transitions, key=lambda row: (row["at"], -row["delta"], row["pr"])
        ),
    }


def episode_metrics(normalized: dict[str, Any]) -> list[dict[str, Any]]:
    observations: list[dict[str, Any]] = []
    for episode in normalized["episodes"]:
        runs = episode["mergeGroupRuns"]
        primary = runs[-1] if runs else None
        required = primary.get("requiredVerification") if primary else None
        enqueue = episode["enqueueTimes"][0] if episode["enqueueTimes"] else None
        dequeue = episode["removalTimes"][-1] if episode["removalTimes"] else None
        merged = episode.get("mergedAt")
        run_created = primary.get("createdAt") if primary else None
        observations.append(
            {
                "pr": episode["pr"],
                "prHeadSha": episode.get("prHeadSha"),
                "enqueueAt": enqueue,
                "mergeGroupCreatedAt": run_created,
                "mergedAt": merged,
                "queueDispatchSeconds": seconds(enqueue, run_created),
                "queueResidenceSeconds": seconds(enqueue, dequeue or merged),
                "endToEndQueueSeconds": seconds(enqueue, merged),
                "mergeGroupRuns": len(runs),
                "requeues": max(0, len(episode["enqueueTimes"]) - 1),
                "mergeGroupConclusion": primary.get("conclusion") if primary else None,
                "mergeGroupRunId": primary.get("runId") if primary else None,
                "mergeGroupSha": primary.get("sha") if primary else None,
                "runnerWaitSeconds": seconds(
                    required.get("createdAt") if required else None,
                    required.get("startedAt") if required else None,
                ),
                "verificationSeconds": seconds(
                    required.get("startedAt") if required else None,
                    required.get("completedAt") if required else None,
                ),
                "postVerificationMergeSeconds": seconds(
                    required.get("completedAt") if required else None,
                    merged,
                ),
            }
        )
    return observations


def extract_metrics(normalized: dict[str, Any]) -> dict[str, Any]:
    """Pure metric extraction from canonical observations."""
    observations = episode_metrics(normalized)
    complete = [row for row in observations if row["enqueueAt"] and row["mergeGroupRunId"]]

    depth = 0
    peak = 0
    for transition in normalized["queueTransitions"]:
        depth = max(0, depth + int(transition["delta"]))
        peak = max(peak, depth)

    all_runs = [
        run
        for episode in normalized["episodes"]
        for run in episode["mergeGroupRuns"]
    ]
    unsuccessful = [
        run for run in all_runs if run.get("conclusion") not in (None, "", "success")
    ]
    unsuccessful_execution_seconds = 0.0
    for run in unsuccessful:
        required = run.get("requiredVerification")
        if required:
            value = seconds(required.get("startedAt"), required.get("completedAt"))
            if value is not None:
                unsuccessful_execution_seconds += value

    return {
        "queueDispatchSeconds": summary(row["queueDispatchSeconds"] for row in complete),
        "queueResidenceSeconds": summary(row["queueResidenceSeconds"] for row in complete),
        "endToEndQueueSeconds": summary(row["endToEndQueueSeconds"] for row in complete),
        "runnerWaitSeconds": summary(row["runnerWaitSeconds"] for row in complete),
        "verificationSeconds": summary(row["verificationSeconds"] for row in complete),
        "postVerificationMergeSeconds": summary(
            row["postVerificationMergeSeconds"] for row in complete
        ),
        "observedPeakQueueDepthLowerBound": peak,
        "requeues": sum(row["requeues"] for row in complete),
        "unsuccessfulMergeGroupRuns": len(unsuccessful),
        "unsuccessfulMergeGroupExecutionSeconds": round(
            unsuccessful_execution_seconds, 3
        ),
        "mergeGroupConclusionCounts": dict(
            sorted(Counter((run.get("conclusion") or "unknown") for run in all_runs).items())
        ),
    }


def project(normalized: dict[str, Any]) -> dict[str, Any]:
    observations = episode_metrics(normalized)
    complete = [row for row in observations if row["enqueueAt"] and row["mergeGroupRunId"]]
    return {
        "schemaVersion": 2,
        "kind": "ordivon.queue-observation-projection",
        "authority": {
            "queue": "GitHub Merge Queue",
            "runs": "GitHub Actions",
            "projection": "tools/repo/queue_telemetry.py",
            "durableLocalQueueState": False,
            "diagnosisAuthority": False,
            "controlAuthority": False,
        },
        "coverage": {
            "repository": normalized["repository"],
            "mergedPullRequestsFetched": len(normalized["episodes"]),
            "queueAttributedPullRequests": len(complete),
            "mergeGroupRunsFetched": sum(
                len(episode["mergeGroupRuns"]) for episode in normalized["episodes"]
            ),
            "historicalDepthIsLowerBound": True,
        },
        "episodes": normalized["episodes"],
        "episodeMetrics": observations,
        "metrics": extract_metrics(normalized),
    }


def analyze(snapshot: ProviderSnapshot) -> dict[str, Any]:
    return project(normalize(snapshot))


def snapshot_from_json(data: dict[str, Any]) -> ProviderSnapshot:
    return ProviderSnapshot(
        repository=data["repository"],
        pulls=data["pulls"],
        timelines=data["timelines"],
        merge_group_runs=data["merge_group_runs"],
        jobs=data["jobs"],
    )


def snapshot_to_json(snapshot: ProviderSnapshot) -> dict[str, Any]:
    return {
        "repository": snapshot.repository,
        "pulls": snapshot.pulls,
        "timelines": snapshot.timelines,
        "merge_group_runs": snapshot.merge_group_runs,
        "jobs": snapshot.jobs,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default="ordivon-org/ordivon")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--input", type=Path, help="analyze a saved provider snapshot")
    parser.add_argument("--snapshot-output", type=Path, help="save raw provider projection")
    parser.add_argument("--normalized-output", type=Path, help="save normalized observation set")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    if args.input:
        snapshot = snapshot_from_json(json.loads(args.input.read_text()))
    else:
        snapshot = Gh(args.repo).collect(args.limit)
    if args.snapshot_output:
        args.snapshot_output.write_text(
            json.dumps(snapshot_to_json(snapshot), indent=2) + "\n"
        )
    normalized = normalize(snapshot)
    if args.normalized_output:
        args.normalized_output.write_text(json.dumps(normalized, indent=2) + "\n")
    result = project(normalized)
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered)
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

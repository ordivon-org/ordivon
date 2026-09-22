#!/usr/bin/env python3
"""Rebuildable GitHub Merge Queue telemetry.

GitHub remains the queue/run authority. This module only projects provider
events into deterministic observations; it owns no queue state or scheduler.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from collections import defaultdict
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
            "gh", "api", "-H", "Accept: application/vnd.github+json",
            "--paginate", "--slurp", endpoint,
        ]
        pages = json.loads(subprocess.run(
            cmd, check=True, text=True, capture_output=True
        ).stdout)
        return [item for page in pages for item in page]

    def collect(self, limit: int) -> ProviderSnapshot:
        owner, repo = self.repo.split("/", 1)
        pulls = self.api(
            f"repos/{owner}/{repo}/pulls?state=closed&sort=updated&direction=desc&per_page={limit}"
        )
        merged = [p for p in pulls if p.get("merged_at")]
        timelines: dict[str, list[dict[str, Any]]] = {}
        for pr in merged:
            n = str(pr["number"])
            timelines[n] = self.paginated_list(f"repos/{owner}/{repo}/issues/{n}/timeline?per_page=100")

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


def _event_time(events: list[dict[str, Any]], name: str, *, first: bool) -> str | None:
    times = [e.get("created_at") for e in events if e.get("event") == name and e.get("created_at")]
    if not times:
        return None
    return min(times) if first else max(times)


def _run_pr(run: dict[str, Any]) -> int | None:
    match = PR_FROM_QUEUE_BRANCH.search(run.get("head_branch") or "")
    return int(match.group(1)) if match else None


def analyze(snapshot: ProviderSnapshot) -> dict[str, Any]:
    runs_by_pr: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for run in snapshot.merge_group_runs:
        pr = _run_pr(run)
        if pr is not None:
            runs_by_pr[pr].append(run)

    observations: list[dict[str, Any]] = []
    depth_events: list[tuple[datetime, int]] = []
    for pr in snapshot.pulls:
        number = int(pr["number"])
        timeline = snapshot.timelines.get(str(number), [])
        enqueues = sorted(
            e["created_at"] for e in timeline
            if e.get("event") == "added_to_merge_queue" and e.get("created_at")
        )
        removals = sorted(
            e["created_at"] for e in timeline
            if e.get("event") == "removed_from_merge_queue" and e.get("created_at")
        )
        for value in enqueues:
            depth_events.append((instant(value), +1))  # type: ignore[arg-type]
        for value in removals:
            depth_events.append((instant(value), -1))  # type: ignore[arg-type]

        runs = sorted(runs_by_pr.get(number, []), key=lambda r: r.get("created_at") or "")
        primary = runs[-1] if runs else None
        run_jobs = snapshot.jobs.get(str(primary["id"]), []) if primary else []
        required = next((j for j in run_jobs if j.get("name") == "root-verification"), None)
        enqueue = enqueues[0] if enqueues else None
        dequeue = removals[-1] if removals else None
        run_created = primary.get("created_at") if primary else None
        merged = pr.get("merged_at")
        observation = {
            "pr": number,
            "enqueueAt": enqueue,
            "mergeGroupCreatedAt": run_created,
            "mergedAt": merged,
            "queueDispatchSeconds": seconds(enqueue, run_created),
            "queueResidenceSeconds": seconds(enqueue, dequeue or merged),
            "endToEndQueueSeconds": seconds(enqueue, merged),
            "mergeGroupRuns": len(runs),
            "requeues": max(0, len(enqueues) - 1),
            "mergeGroupConclusion": primary.get("conclusion") if primary else None,
            "mergeGroupRunId": primary.get("id") if primary else None,
            "mergeGroupSha": primary.get("head_sha") if primary else None,
            "runnerWaitSeconds": seconds(
                required.get("created_at") if required else None,
                required.get("started_at") if required else None,
            ),
            "verificationSeconds": seconds(
                required.get("started_at") if required else None,
                required.get("completed_at") if required else None,
            ),
            "postVerificationMergeSeconds": seconds(
                required.get("completed_at") if required else None,
                merged,
            ),
        }
        observations.append(observation)

    # Reconstructed depth is a lower bound when collection starts after an
    # already-enqueued item. Clamp below zero and expose the limitation.
    depth = 0
    peak = 0
    for _, delta in sorted(depth_events, key=lambda x: (x[0], -x[1])):
        depth = max(0, depth + delta)
        peak = max(peak, depth)

    all_runs = [r for r in snapshot.merge_group_runs if _run_pr(r) is not None]
    unsuccessful = [r for r in all_runs if r.get("conclusion") not in (None, "", "success")]
    wasted_seconds = 0.0
    for run in unsuccessful:
        for job in snapshot.jobs.get(str(run["id"]), []):
            value = seconds(job.get("started_at"), job.get("completed_at"))
            if value is not None:
                wasted_seconds += value

    complete = [o for o in observations if o["enqueueAt"] and o["mergeGroupRunId"]]
    return {
        "schemaVersion": 1,
        "authority": {
            "queue": "GitHub Merge Queue",
            "runs": "GitHub Actions",
            "projection": "tools/repo/queue_telemetry.py",
            "durableLocalQueueState": False,
        },
        "coverage": {
            "repository": snapshot.repository,
            "mergedPullRequestsFetched": len(snapshot.pulls),
            "queueAttributedPullRequests": len(complete),
            "mergeGroupRunsFetched": len(snapshot.merge_group_runs),
            "historicalDepthIsLowerBound": True,
        },
        "metrics": {
            "queueDispatchSeconds": summary(o["queueDispatchSeconds"] for o in complete),
            "queueResidenceSeconds": summary(o["queueResidenceSeconds"] for o in complete),
            "endToEndQueueSeconds": summary(o["endToEndQueueSeconds"] for o in complete),
            "runnerWaitSeconds": summary(o["runnerWaitSeconds"] for o in complete),
            "verificationSeconds": summary(o["verificationSeconds"] for o in complete),
            "postVerificationMergeSeconds": summary(o["postVerificationMergeSeconds"] for o in complete),
            "observedPeakQueueDepthLowerBound": peak,
            "requeues": sum(o["requeues"] for o in complete),
            "unsuccessfulMergeGroupRuns": len(unsuccessful),
            "observedWastedVerificationSeconds": round(wasted_seconds, 3),
        },
        "pressureGate": {
            "adaptiveSpeculation": "INSUFFICIENT_EVIDENCE",
            "batchingBisection": "INSUFFICIENT_EVIDENCE",
            "costPrediction": "INSUFFICIENT_HISTORY",
            "reason": (
                "Telemetry is observational. A scheduler change requires repeated "
                "contention or material CI waste plus enough history to validate it."
            ),
        },
        "observations": sorted(observations, key=lambda x: x["pr"]),
    }


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
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    if args.input:
        snapshot = snapshot_from_json(json.loads(args.input.read_text()))
    else:
        snapshot = Gh(args.repo).collect(args.limit)
    if args.snapshot_output:
        args.snapshot_output.write_text(json.dumps(snapshot_to_json(snapshot), indent=2) + "\n")
    result = analyze(snapshot)
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered)
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

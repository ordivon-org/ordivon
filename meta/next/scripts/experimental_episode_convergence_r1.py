#!/usr/bin/env python3
"""Convergence Observation R2 -> Experimental Episode R1 adapter.

This adapter lowers rebuildable Queue/CI observation projections into the existing
Experimental Episode analytical contract. GitHub remains provider authority and the
Episode/PostgreSQL layer remains a derived analytical consumer with no scheduling,
merge, cancellation, evidence-reuse, or domain authority.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from ordivon_composition import canonical_digest

if __package__:
    from scripts.experimental_episode_r1 import validate_episode
else:
    from experimental_episode_r1 import validate_episode

QUEUE_PROFILE = "convergence-queue-observation-v1"
CI_PROFILE = "convergence-ci-observation-v1"


def _require_projection(value: dict[str, Any], *, kind: str) -> None:
    if value.get("kind") != kind:
        raise ValueError(f"expected {kind}, got {value.get('kind')!r}")


def _measure(name: str, value: Any, unit: str | None = None) -> dict[str, Any] | None:
    if value is None or isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    row: dict[str, Any] = {"name": name, "value": value}
    if unit is not None:
        row["unit"] = unit
    return row


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return slug or "unnamed"


def _finalize(value: dict[str, Any]) -> dict[str, Any]:
    value["projectionDigest"] = canonical_digest(value)
    validate_episode(value)
    return value


def project_queue_episode(
    projection: dict[str, Any], episode: dict[str, Any]
) -> dict[str, Any]:
    _require_projection(projection, kind="ordivon.queue-observation-projection")
    repository = projection["coverage"]["repository"]
    pr = int(episode["pr"])
    metric = next(
        (row for row in projection.get("episodeMetrics", []) if int(row["pr"]) == pr),
        {},
    )
    merge_runs = episode.get("mergeGroupRuns", [])
    source_record = {"episode": episode, "metrics": metric}

    owner_refs: list[dict[str, Any]] = []
    head_sha = episode.get("prHeadSha")
    if isinstance(head_sha, str) and head_sha:
        owner_refs.append(
            {
                "ownerId": "git",
                "objectKind": "revision",
                "objectId": head_sha,
                "relation": "pull-request-head",
            }
        )
    for run in merge_runs:
        run_id = run.get("runId")
        if run_id is not None:
            owner_refs.append(
                {
                    "ownerId": "github-actions",
                    "objectKind": "workflow-run",
                    "objectId": str(run_id),
                    "relation": "merge-group-verification",
                }
            )
        sha = run.get("sha")
        if isinstance(sha, str) and sha:
            owner_refs.append(
                {
                    "ownerId": "git",
                    "objectKind": "revision",
                    "objectId": sha,
                    "relation": "merge-group-revision",
                }
            )

    dimensions = [
        {"name": "queue.repository", "value": repository},
        {
            "name": "queue.provider",
            "value": projection.get("authority", {}).get("queue"),
        },
        {"name": "queue.pr", "value": pr},
        {"name": "queue.merged_at", "value": episode.get("mergedAt")},
        {
            "name": "queue.merge_group_conclusion",
            "value": metric.get("mergeGroupConclusion"),
        },
    ]
    measures = [
        _measure("queue.merge_group_runs", metric.get("mergeGroupRuns"), "runs"),
        _measure("queue.requeues", metric.get("requeues"), "count"),
        _measure(
            "queue.dispatch_seconds", metric.get("queueDispatchSeconds"), "seconds"
        ),
        _measure(
            "queue.residence_seconds", metric.get("queueResidenceSeconds"), "seconds"
        ),
        _measure(
            "queue.end_to_end_seconds", metric.get("endToEndQueueSeconds"), "seconds"
        ),
        _measure(
            "queue.runner_wait_seconds", metric.get("runnerWaitSeconds"), "seconds"
        ),
        _measure(
            "queue.verification_seconds", metric.get("verificationSeconds"), "seconds"
        ),
        _measure(
            "queue.post_verification_merge_seconds",
            metric.get("postVerificationMergeSeconds"),
            "seconds",
        ),
    ]

    return _finalize(
        {
            "schemaVersion": 1,
            "kind": "ordivon.experimental-episode-binding",
            "profileId": QUEUE_PROFILE,
            "episodeId": f"episode:convergence-queue:{repository}:pr:{pr}",
            "dataClass": "EXPERIENCE",
            "anchor": {
                "ownerId": "github",
                "objectKind": "pull-request",
                "objectId": f"{repository}#{pr}",
                "sourceRecordDigest": canonical_digest(source_record),
            },
            "ownerRefs": owner_refs,
            "evidenceBindings": [
                {
                    "kind": "github-merge-group-runs",
                    "count": len(merge_runs),
                    "setDigest": canonical_digest(merge_runs),
                },
                {
                    "kind": "queue-episode-metrics",
                    "count": 1 if metric else 0,
                    "setDigest": canonical_digest([metric] if metric else []),
                },
            ],
            "dimensions": dimensions,
            "measures": [row for row in measures if row is not None],
            "unresolved": [
                "Historical reconstructed queue depth remains a lower bound.",
                "Queue timing does not establish CI economic usefulness or waste.",
            ],
            "nonClaims": [
                "Episode is not GitHub Merge Queue truth.",
                "Episode does not grant scheduling or merge authority.",
                "Queue success does not establish domain acceptance.",
            ],
        }
    )


def project_ci_run(projection: dict[str, Any], run: dict[str, Any]) -> dict[str, Any]:
    _require_projection(projection, kind="ordivon.ci-observation-projection")
    repository = projection["coverage"]["repository"]
    run_id = str(run["runId"])
    jobs = run.get("jobs", [])
    steps = [step for job in jobs for step in job.get("steps", [])]

    owner_refs: list[dict[str, Any]] = []
    head_sha = run.get("headSha")
    if isinstance(head_sha, str) and head_sha:
        owner_refs.append(
            {
                "ownerId": "git",
                "objectKind": "revision",
                "objectId": head_sha,
                "relation": "ci-head-revision",
            }
        )
    for job in jobs:
        if job.get("jobId") is not None:
            owner_refs.append(
                {
                    "ownerId": "github-actions",
                    "objectKind": "job",
                    "objectId": str(job["jobId"]),
                    "relation": "workflow-job",
                }
            )

    dimensions = [
        {"name": "ci.repository", "value": repository},
        {"name": "ci.event", "value": run.get("event")},
        {"name": "ci.workflow_name", "value": run.get("workflowName")},
        {"name": "ci.status", "value": run.get("status")},
        {"name": "ci.conclusion", "value": run.get("conclusion")},
        {"name": "ci.termination_reason", "value": run.get("terminationReason")},
        {"name": "ci.economic_outcome", "value": run.get("economicOutcome")},
        {"name": "ci.run_attempt", "value": run.get("runAttempt")},
    ]

    measures: list[dict[str, Any] | None] = [
        _measure("ci.wall_seconds", run.get("wallSeconds"), "seconds"),
        _measure("ci.jobs", len(jobs), "jobs"),
        _measure("ci.steps", len(steps), "steps"),
    ]
    root_jobs = [job for job in jobs if job.get("name") == "root-verification"]
    if root_jobs:
        root = root_jobs[-1]
        measures.extend(
            [
                _measure(
                    "ci.root_verification.runner_wait_seconds",
                    root.get("runnerWaitSeconds"),
                    "seconds",
                ),
                _measure(
                    "ci.root_verification.execution_seconds",
                    root.get("executionSeconds"),
                    "seconds",
                ),
            ]
        )
        seen_step_names: dict[str, int] = {}
        for step in root.get("steps", []):
            duration = step.get("durationSeconds")
            if duration is None:
                continue
            base = _slug(str(step.get("name") or "unnamed"))
            seen_step_names[base] = seen_step_names.get(base, 0) + 1
            suffix = "" if seen_step_names[base] == 1 else f"_{seen_step_names[base]}"
            measures.append(
                _measure(
                    f"ci.root_verification.step.{base}{suffix}.seconds",
                    duration,
                    "seconds",
                )
            )

    return _finalize(
        {
            "schemaVersion": 1,
            "kind": "ordivon.experimental-episode-binding",
            "profileId": CI_PROFILE,
            "episodeId": f"episode:convergence-ci:{repository}:run:{run_id}",
            "dataClass": "EXPERIENCE",
            "anchor": {
                "ownerId": "github-actions",
                "objectKind": "workflow-run",
                "objectId": run_id,
                "sourceRecordDigest": canonical_digest(run),
            },
            "ownerRefs": owner_refs,
            "evidenceBindings": [
                {
                    "kind": "github-actions-jobs",
                    "count": len(jobs),
                    "setDigest": canonical_digest(jobs),
                },
                {
                    "kind": "github-actions-steps",
                    "count": len(steps),
                    "setDigest": canonical_digest(steps),
                },
            ],
            "dimensions": dimensions,
            "measures": [row for row in measures if row is not None],
            "unresolved": [
                "Provider conclusion is not CI economic outcome.",
                "UNCLASSIFIED economic outcome requires separate evidence before optimization admission.",
            ],
            "nonClaims": [
                "Episode is not GitHub Actions run truth.",
                "Episode does not cancel, retry, deduplicate, or reuse CI work.",
                "CI success or failure does not establish domain acceptance.",
            ],
        }
    )


def project_convergence(
    queue_projection: dict[str, Any], ci_projection: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    _require_projection(queue_projection, kind="ordivon.queue-observation-projection")
    _require_projection(ci_projection, kind="ordivon.ci-observation-projection")
    if (
        queue_projection["coverage"]["repository"]
        != ci_projection["coverage"]["repository"]
    ):
        raise ValueError("queue and CI projections must describe the same repository")

    queue_episodes = [
        project_queue_episode(queue_projection, row)
        for row in queue_projection.get("episodes", [])
    ]
    ci_episodes = [
        project_ci_run(ci_projection, row) for row in ci_projection.get("runs", [])
    ]
    queue_ids = [row["episodeId"] for row in queue_episodes]
    ci_ids = [row["episodeId"] for row in ci_episodes]
    collisions = (len(queue_ids) - len(set(queue_ids))) + (
        len(ci_ids) - len(set(ci_ids))
    )
    summary: dict[str, Any] = {
        "schemaVersion": 1,
        "kind": "ordivon.convergence-experimental-episode-projection-summary",
        "repository": queue_projection["coverage"]["repository"],
        "queueProfileId": QUEUE_PROFILE,
        "ciProfileId": CI_PROFILE,
        "queueEpisodes": len(queue_episodes),
        "ciEpisodes": len(ci_episodes),
        "episodeIdentityCollisions": collisions,
        "queueEpisodeIdSetDigest": canonical_digest(sorted(queue_ids)),
        "queueProjectionDigestSetDigest": canonical_digest(
            sorted(row["projectionDigest"] for row in queue_episodes)
        ),
        "ciEpisodeIdSetDigest": canonical_digest(sorted(ci_ids)),
        "ciProjectionDigestSetDigest": canonical_digest(
            sorted(row["projectionDigest"] for row in ci_episodes)
        ),
        "standing": (
            "PASS_CONVERGENCE_EPISODE_PROJECTION"
            if collisions == 0
            else "FAIL_CONVERGENCE_EPISODE_IDENTITY_COLLISION"
        ),
        "claimBoundary": (
            "This is a rebuildable analytical projection into the existing Experimental Episode contract. "
            "GitHub remains Queue/Actions authority and PostgreSQL remains a derived consumer."
        ),
    }
    summary["summaryDigest"] = canonical_digest(summary)
    return queue_episodes, ci_episodes, summary


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(
            json.dumps(row, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
            + "\n"
            for row in rows
        ),
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("queue", type=Path)
    parser.add_argument("ci", type=Path)
    parser.add_argument("queue_episodes", type=Path)
    parser.add_argument("ci_episodes", type=Path)
    parser.add_argument("summary", type=Path)
    args = parser.parse_args()

    queue = json.loads(args.queue.read_text(encoding="utf-8"))
    ci = json.loads(args.ci.read_text(encoding="utf-8"))
    queue_episodes, ci_episodes, summary = project_convergence(queue, ci)
    _write_jsonl(args.queue_episodes, queue_episodes)
    _write_jsonl(args.ci_episodes, ci_episodes)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    if summary["standing"] != "PASS_CONVERGENCE_EPISODE_PROJECTION":
        raise SystemExit(summary["standing"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

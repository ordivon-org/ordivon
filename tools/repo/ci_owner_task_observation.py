#!/usr/bin/env python3
"""Qualify descriptive native task-group spans against an explicit shard plan.

The caller supplies the expected ordered plan and the native Run/Attempt/Job
metadata and corresponding job log. Neither the plan nor log proves execution
of individual tests, the tested merge tree, or authority to schedule work.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from statistics import median
from typing import Any

from ci_owner_shards import MAX_SHARDS

MAX_LOG_BYTES = 32 * 1024 * 1024
MAX_CONTEXT_BYTES = 1024 * 1024
STAMP = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,9})?(?:Z|[+-][0-9]{2}:[0-9]{2})")
TASK = re.compile(r"[a-zA-Z0-9_:-]+")
MARKER = re.compile(r"^(\S+)\s+##\[(group|endgroup)\](.*)$")
ANSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


def _instant(value: Any, *, whole_second: bool = False) -> datetime:
    if not isinstance(value, str) or STAMP.fullmatch(value) is None:
        raise ValueError("unqualified native timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("unqualified native timestamp") from exc
    if parsed.utcoffset() is None or (whole_second and "." in value):
        raise ValueError("unqualified native timestamp precision")
    return parsed


def _ms(start: datetime, end: datetime) -> int:
    delta = end - start
    micros = delta.days * 86_400_000_000 + delta.seconds * 1_000_000 + delta.microseconds
    if micros < 0:
        raise ValueError("reversed native interval")
    return (micros + 999) // 1000


def _positive_id(value: Any) -> bool:
    return type(value) is int and value > 0


def _successful(row: dict[str, Any]) -> bool:
    return row.get("status") == "completed" and row.get("conclusion") == "success"


def observe_task_groups(
    run: dict[str, Any], job: dict[str, Any], plan: dict[str, Any], log: bytes,
) -> dict[str, Any]:
    if not all(isinstance(x, dict) for x in (run, job, plan)):
        raise ValueError("malformed task observation context")
    run_id, attempt, head = run.get("id"), run.get("run_attempt"), run.get("head_sha")
    if (
        not _positive_id(run_id) or not _positive_id(attempt)
        or not isinstance(head, str) or re.fullmatch(r"[a-f0-9]{40}", head) is None
        or run.get("path") != ".github/workflows/ci.yml" or not _successful(run)
    ):
        raise ValueError("unqualified workflow identity or conclusion")
    shard, tasks = plan.get("shard"), plan.get("tasks")
    if (
        set(plan) != {"shard", "tasks"} or type(shard) is not int or shard < 0
        or not isinstance(tasks, list) or not tasks
        or not all(isinstance(t, str) and TASK.fullmatch(t) and t != "formal:verify" for t in tasks)
        or len(tasks) != len(set(tasks))
    ):
        raise ValueError("unqualified expected Owner task plan")
    if (
        not _positive_id(job.get("id")) or not _positive_id(job.get("run_id"))
        or not _positive_id(job.get("run_attempt")) or job["run_id"] != run_id
        or job["run_attempt"] != attempt or job.get("head_sha") != head
        or job.get("name") != f"owner-shard-{shard}" or not _successful(job)
    ):
        raise ValueError("unqualified native Owner job")
    steps = job.get("steps")
    if not isinstance(steps, list) or not all(isinstance(step, dict) for step in steps):
        raise ValueError("unqualified native job steps")
    matches = [step for step in steps if step.get("name") == "Verify affected owners"]
    if len(matches) != 1 or not _successful(matches[0]) or not _positive_id(matches[0].get("number")):
        raise ValueError("unqualified native Owner verification step")
    step = matches[0]
    job_start, start, end, job_end = (
        _instant(value, whole_second=True) for value in (
            job.get("started_at"), step.get("started_at"),
            step.get("completed_at"), job.get("completed_at"),
        )
    )
    if not job_start <= start <= end <= job_end:
        raise ValueError("Owner step is outside native job")
    if not isinstance(log, bytes) or not 0 < len(log) <= MAX_LOG_BYTES:
        raise ValueError("unqualified native log byte length")
    rows = []
    active = None
    depth = 0
    last = None
    # REST exposes whole seconds. A log marker in the reported completion
    # second is admissible, not proof of finer provider step boundaries.
    limit = end + timedelta(seconds=1)
    # Avoid a second full-log string and a list of every line; no raw log
    # content enters the result. The input byte bound also bounds a long line.
    for raw_line in io.BytesIO(log):
        try:
            line = ANSI.sub("", raw_line.decode("utf-8").rstrip("\r\n"))
        except UnicodeError as exc:
            raise ValueError("invalid native log encoding") from exc
        marker = MARKER.fullmatch(line)
        if marker is None:
            continue
        stamp = _instant(marker[1])
        if not start <= stamp < limit:
            continue
        kind, label = marker[2], marker[3]
        if kind == "group" and label == "mise run":
            raise ValueError("missing native task group label")
        task = label.removeprefix("mise run ") if kind == "group" and label.startswith("mise run ") else None
        if task is not None:
            if (
                active is not None or TASK.fullmatch(task) is None
                or len(rows) >= len(tasks) or task != tasks[len(rows)]
                or (last is not None and stamp < last)
            ):
                raise ValueError("unexpected or nested native Owner task group")
            active = (task, marker[1], stamp)
            depth = 1
            last = stamp
        elif active is not None:
            if kind == "endgroup" and label.strip():
                raise ValueError("malformed native endgroup marker")
            if stamp < last:
                raise ValueError("reversed native Owner group markers")
            last = stamp
            if kind == "group":
                depth += 1
            else:
                depth -= 1
                if depth == 0:
                    name, raw_start, t0 = active
                    duration = _ms(t0, stamp)
                    if duration <= 0:
                        raise ValueError("nonpositive observed task group span")
                    rows.append({
                        "task": name, "startedAt": raw_start, "completedAt": marker[1],
                        "elapsedMs": duration,
                    })
                    active = None
    if active is not None or len(rows) != len(tasks):
        raise ValueError("incomplete native Owner task groups")
    weights = {row["task"]: row["elapsedMs"] for row in rows}
    return {
        "standing": "DESCRIPTIVE_GROUP_SPANS_NOT_RECEIPTS",
        "timestampScope": "REST_SECOND_BUCKET_LOG_MICROSECOND",
        "runId": run_id, "runAttempt": attempt, "providerHeadSha": head,
        "jobId": job["id"], "shard": shard, "stepNumber": step["number"],
        "logSha256": hashlib.sha256(log).hexdigest(),
        "expectedTasks": list(tasks),
        "groups": rows, "taskMilliseconds": weights,
        "groupObservedMs": sum(weights.values()),
        "fixedObservedMs": _ms(job_start, start) + _ms(end, job_end),
        "namedStepMs": _ms(start, end),
    }


def observe_task_cohort(
    run: dict[str, Any], jobs: list[dict[str, Any]], matrix: dict[str, Any],
    logs: dict[int, bytes],
) -> dict[str, Any]:
    """Conserve the complete caller-supplied Owner matrix across observed jobs.

    The jobs list must contain only the expected Owner jobs. Provider page
    completeness and exact historical plan derivation remain caller obligations.
    """
    if not isinstance(matrix, dict) or set(matrix) != {"include"}:
        raise ValueError("invalid expected Owner matrix")
    plans = matrix["include"]
    if (
        not isinstance(plans, list) or not 1 <= len(plans) <= MAX_SHARDS
        or not all(isinstance(p, dict) and type(p.get("shard")) is int for p in plans)
        or [p["shard"] for p in plans] != list(range(len(plans)))
    ):
        raise ValueError("invalid expected Owner matrix shards")
    if not isinstance(jobs, list) or len(jobs) != len(plans):
        raise ValueError("incomplete Owner job cohort")
    by_name = {}
    ids = set()
    for job in jobs:
        if (
            not isinstance(job, dict) or not _positive_id(job.get("id"))
            or not isinstance(job.get("name"), str)
            or job["name"] in by_name or job["id"] in ids
        ):
            raise ValueError("duplicate or malformed Owner job")
        by_name[job["name"]] = job
        ids.add(job["id"])
    expected_names = {f"owner-shard-{p['shard']}" for p in plans}
    if set(by_name) != expected_names:
        raise ValueError("Owner job identities do not match expected matrix")
    if not isinstance(logs, dict) or any(not _positive_id(k) for k in logs) or set(logs) != ids:
        raise ValueError("Owner job logs do not match expected job identities")

    if any(not isinstance(raw, bytes) for raw in logs.values()) or sum(map(len, logs.values())) > MAX_LOG_BYTES:
        raise ValueError("Owner cohort log byte length exceeds bound")

    reports = []
    tasks = []
    weights = {}
    for plan in plans:
        job = by_name[f"owner-shard-{plan['shard']}"]
        report = observe_task_groups(run, job, plan, logs[job["id"]])
        if set(weights).intersection(report["taskMilliseconds"]):
            raise ValueError("duplicate task across expected Owner shards")
        tasks.extend(report["expectedTasks"])
        weights.update(report["taskMilliseconds"])
        reports.append(report)
    fixed = [r["fixedObservedMs"] for r in reports]
    # Whole-second native bounds guarantee an integral-millisecond median.
    return {
        "standing": "DESCRIPTIVE_COHORT_NOT_EXECUTION_ATTESTATION",
        "runId": run["id"], "runAttempt": run["run_attempt"],
        "providerHeadSha": run["head_sha"],
        "fixedObservedMs": fixed,
        "scenario": {
            "tasks": tasks, "taskMilliseconds": weights,
            "fixedMilliseconds": int(median(fixed)),
        },
        "shards": reports,
    }


def _bounded_read(path: Path, limit: int) -> bytes:
    with path.open("rb") as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise ValueError("observation input exceeds bound")
    return data


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate observation context key")
        result[key] = value
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("context", type=Path, help="JSON with run, job, and expected plan")
    parser.add_argument("log", type=Path, help="native job log, or directory of JOB_ID.log files for a cohort")
    args = parser.parse_args()
    context = json.loads(_bounded_read(args.context, MAX_CONTEXT_BYTES), object_pairs_hook=_unique_object)
    if not isinstance(context, dict):
        raise ValueError("unqualified observation context fields")
    if set(context) == {"run", "job", "plan"}:
        result = observe_task_groups(
            context["run"], context["job"], context["plan"],
            _bounded_read(args.log, MAX_LOG_BYTES),
        )
    elif set(context) == {"run", "jobs", "matrix"}:
        jobs = context["jobs"]
        if (
            not isinstance(jobs, list) or not 1 <= len(jobs) <= MAX_SHARDS
            or not all(isinstance(j, dict) and _positive_id(j.get("id")) for j in jobs)
            or len({j["id"] for j in jobs}) != len(jobs)
        ):
            raise ValueError("unqualified Owner cohort context")
        # Bound the entire offline cohort, not merely each individual file.
        logs = {}
        remaining = MAX_LOG_BYTES
        for job in jobs:
            logs[job["id"]] = _bounded_read(args.log / f"{job['id']}.log", remaining)
            remaining -= len(logs[job["id"]])
        result = observe_task_cohort(context["run"], jobs, context["matrix"], logs)
    else:
        raise ValueError("unqualified observation context fields")
    print(json.dumps(result, separators=(",", ":"), sort_keys=True))


if __name__ == "__main__":
    main()

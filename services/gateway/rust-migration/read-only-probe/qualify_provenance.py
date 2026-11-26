"""Independent relational oracle for native terminal Artifact provenance."""

from __future__ import annotations

import copy
import random

from qualify_semantics import independent_descriptor


def oracle(x):
    i, o = x["inspection"], x["observation"]
    j = i["job"]
    a = i.get("attempts")
    if (
        type(i.get("schemaVersion")) is not int
        or i["schemaVersion"] != 2
        or type(i.get("migrationVersion")) is not int
        or i["migrationVersion"] != 0
        or j.get("jobId") != x["jobId"]
        or j.get("clientRequestId") != x["scopedKey"]
        or j.get("mechanicallyConverged") is not True
        or i.get("attemptsTruncated") is not False
        or not isinstance(a, list)
        or len(a) != 1
    ):
        return None
    a = a[0]
    count = i["artifacts"].get("count")
    if type(count) is not int or not 0 <= count < 2**64:
        return None
    if type(a.get("artifactCount")) is not int or a["artifactCount"] != count:
        return None
    pairs = (
        (j.get("operationDigest"), o.get("operationDigest")),
        (j.get("resolution"), o.get("executionDisposition")),
        (a.get("attemptId"), o.get("attemptId")),
        (a.get("state"), o.get("attemptState")),
    )
    if any(
        not isinstance(left, str) or not left or left.strip() != left or left != right
        for left, right in pairs
    ):
        return None
    if (
        o.get("jobId") != x["jobId"]
        or o.get("executionTerminal") is not True
        or o.get("deliveryDisposition") != "committed"
        or o.get("recoveryRequired") is not False
        or o.get("artifactsAvailable") is not True
    ):
        return None
    q = independent_descriptor(o, count)
    if not q["metadata_complete"]:
        return None
    rows = q["descriptors"]
    if any(d["attemptId"] != a["attemptId"] for d in rows):
        return None
    return next((d for d in rows if d["artifactId"] == x["artifactId"]), None)


def add_provenance_cases(add):
    rng = random.Random(20261126)
    mutations = [
        ("inspection.schemaVersion", 3),
        ("inspection.schemaVersion", 2.0),
        ("inspection.migrationVersion", False),
        ("inspection.job.jobId", "other"),
        ("inspection.job.clientRequestId", "other"),
        ("inspection.job.mechanicallyConverged", 1),
        ("inspection.attemptsTruncated", None),
        ("inspection.attempts", []),
        ("inspection.attempts.0.artifactCount", True),
        ("inspection.artifacts.count", None),
        ("observation.jobId", "other"),
        ("observation.operationDigest", "other"),
        ("observation.attemptId", "other"),
        ("observation.attemptState", "running"),
        ("observation.executionDisposition", "failed"),
        ("observation.executionTerminal", 1),
        ("observation.deliveryDisposition", "unknown"),
        ("observation.recoveryRequired", None),
        ("observation.artifactsAvailable", False),
        ("observation.artifacts.0.attemptId", "other"),
        ("observation.artifacts.0.digest", "invalid"),
        ("observation.artifacts.0.retainedBytes", -1),
        ("artifactId", "missing"),
    ]

    def case(x):
        add("artifact_provenance", x, oracle(x))

    for n in range(128):
        count = rng.randrange(1, 6)
        rows = [
            dict(
                artifactId=f"opaque-{n}-{k}",
                attemptId="a",
                kind="future-kind",
                digest="sha256:" + "a" * 64,
                retainedBytes=rng.randrange(2**64),
                truncated=bool(k % 2),
            )
            for k in range(count)
        ]
        x = dict(
            jobId="j",
            scopedKey="k",
            artifactId=rows[-1]["artifactId"],
            inspection=dict(
                schemaVersion=2,
                migrationVersion=0,
                attemptsTruncated=False,
                job=dict(
                    jobId="j",
                    clientRequestId="k",
                    operationDigest="op",
                    mechanicallyConverged=True,
                    resolution="succeeded",
                ),
                attempts=[dict(attemptId="a", state="succeeded", artifactCount=count)],
                artifacts=dict(count=count),
            ),
            observation=dict(
                jobId="j",
                operationDigest="op",
                attemptId="a",
                attemptState="succeeded",
                executionDisposition="succeeded",
                executionTerminal=True,
                deliveryDisposition="committed",
                recoveryRequired=False,
                artifactsAvailable=True,
                artifacts=rows,
            ),
        )
        case(x)
        y = copy.deepcopy(x)
        y["observation"]["artifacts"].reverse()
        case(y)
        y = copy.deepcopy(x)
        y["observation"]["artifacts"] += [rows[0]]
        case(y)
        for path, value in mutations:
            y = copy.deepcopy(x)
            obj = y
            *prefix, last = path.split(".")
            for key in prefix:
                obj = obj[int(key)] if isinstance(obj, list) else obj[key]
            obj[last] = value
            case(y)

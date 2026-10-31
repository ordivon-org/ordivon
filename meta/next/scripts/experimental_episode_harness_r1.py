#!/usr/bin/env python3
"""Harness RSI -> Experimental Episode R1 adapter.

This adapter consumes compact historical Harness RSI acceptance receipts. It does not
reinterpret Harness journals or Runtime jobs; it only binds exact receipt identity,
declared Runtime job references, stable scalar dimensions, and bounded numeric measures.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any

from ordivon_composition import canonical_digest

from scripts.experimental_episode_r1 import validate_episode

RUNTIME_JOB_KEYS = {
    "runtimeJobId",
    "sourceCommitEvaluationJobId",
    "evaluatorRegressionJobId",
    "currentReleaseGateJobId",
    "evaluationRecordJobId",
    "agentRuntimeJobId",
    "materializationJobId",
    "baselineRuntimeJobId",
    "repairVerificationRuntimeJobId",
    "measurementRuntimeJobId",
}

# The receipt is NOT a trusted source of public free-form strings. Only
# structural identifiers enter the analytical projection; the full source
# remains represented by sourceRecordDigest, never by copied payload bytes.
PUBLIC_KIND = re.compile(r"ordivon\.harness-rsi-[a-z0-9][a-z0-9-]{0,95}\Z")
PUBLIC_SOURCE_NAME = re.compile(r"harness-rsi-p[a-z0-9][a-z0-9-]{0,95}\.json\Z")
GIT_REVISION = re.compile(r"[0-9a-f]{40}(?:[0-9a-f]{24})?\Z")
RUNTIME_JOB_ID = re.compile(r"job-[A-Za-z0-9][A-Za-z0-9-]{0,71}\Z")
PUBLIC_STATUSES = frozenset({"accepted", "falsified", "blocked", "failed", "rejected"})


MEASURE_KEYS = {
    "rounds",
    "observationCount",
    "p4ObservationBaseline",
    "observationReductionFactor",
    "completedProviderCalls",
    "providerCalls",
    "totalTokens",
    "promptTokens",
    "completionTokens",
    "promptCacheHitTokens",
    "fullTestsPassed",
    "focusedTestsPassed",
    "testsPassed",
    "testsSkipped",
    "exactEditCount",
}


def _walk_named_scalars(
    value: Any,
    *,
    wanted: set[str],
    path: tuple[str, ...] = (),
) -> list[tuple[str, Any]]:
    found: list[tuple[str, Any]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            next_path = (*path, key)
            if key in wanted and isinstance(item, (str, int, float, bool)):
                found.append((".".join(next_path), item))
            found.extend(_walk_named_scalars(item, wanted=wanted, path=next_path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            found.extend(
                _walk_named_scalars(item, wanted=wanted, path=(*path, str(index)))
            )
    return found


def project_harness_rsi_record(
    record: dict[str, Any], *, source_name: str
) -> dict[str, Any]:
    kind = record.get("kind")
    status = record.get("status")
    if not isinstance(kind, str) or PUBLIC_KIND.fullmatch(kind) is None:
        raise ValueError("Harness RSI kind is not a qualified public identifier")
    if not isinstance(status, str) or status not in PUBLIC_STATUSES:
        raise ValueError("Harness RSI status is not a qualified lifecycle value")
    if PUBLIC_SOURCE_NAME.fullmatch(source_name) is None:
        raise ValueError("Harness RSI source_name is not a bounded receipt basename")

    candidate_jobs = _walk_named_scalars(record, wanted=RUNTIME_JOB_KEYS)
    runtime_jobs: list[str] = []
    for field, value in candidate_jobs:
        if not isinstance(value, str) or RUNTIME_JOB_ID.fullmatch(value) is None:
            # Never echo unqualified source bytes in a parser diagnostic.
            raise ValueError(f"Harness RSI runtime reference at {field} is unqualified")
        runtime_jobs.append(value)
    runtime_jobs = sorted(set(runtime_jobs))

    owner_refs: list[dict[str, Any]] = []
    for field, relation in (
        ("baseRevision", "base-revision"),
        ("implementationRevision", "implementation-revision"),
        ("documentationRevision", "documentation-revision"),
        ("testHardeningRevision", "test-hardening-revision"),
    ):
        revision = record.get(field)
        if revision is not None:
            if (
                not isinstance(revision, str)
                or GIT_REVISION.fullmatch(revision) is None
            ):
                raise ValueError(f"Harness RSI {field} is not a full Git revision")
            owner_refs.append(
                {
                    "ownerId": "git",
                    "objectKind": "revision",
                    "objectId": revision,
                    "relation": relation,
                }
            )

    for job_id in runtime_jobs:
        owner_refs.append(
            {
                "ownerId": "runtime",
                "objectKind": "job",
                "objectId": job_id,
                "relation": "cited-runtime-job",
            }
        )

    dimensions = [
        {"name": "harness.acceptance_kind", "value": kind},
        {"name": "harness.acceptance_status", "value": status},
        {"name": "harness.source_name", "value": source_name},
    ]
    # The receipt does not attest that modelId/researchOutcome are non-secret.
    # Arbitrary source strings cannot be promoted to public dimensions merely
    # because their field name sounds benign. Digest the source, omit the value.
    measures: list[dict[str, Any]] = []
    for path, value in _walk_named_scalars(record, wanted=MEASURE_KEYS):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"Harness RSI measure {path} is not numeric")
        # Bounded resource observations only; arbitrary long numeric values
        # cannot be smuggled into an otherwise approved measure dimension.
        if not math.isfinite(value) or not 0 <= value <= 1_000_000_000_000:
            raise ValueError(f"Harness RSI measure {path} is not finite/bounded")
        measures.append({"name": f"harness.{path}", "value": value})

    source_digest = canonical_digest(record)
    result: dict[str, Any] = {
        "schemaVersion": 1,
        "kind": "ordivon.experimental-episode-binding",
        "profileId": "harness-rsi-acceptance-v1",
        "episodeId": f"episode:harness-rsi:{source_name.removesuffix('.json')}",
        "dataClass": "EXPERIENCE",
        "anchor": {
            "ownerId": "harness-evidence",
            "objectKind": "rsi-acceptance-receipt",
            "objectId": source_name,
            "sourceRecordDigest": source_digest,
        },
        "ownerRefs": owner_refs,
        "evidenceBindings": [
            {
                "kind": "harness-acceptance-receipt",
                "count": 1,
                "setDigest": source_digest,
            },
            {
                "kind": "cited-runtime-jobs",
                "count": len(runtime_jobs),
                "setDigest": canonical_digest(runtime_jobs),
            },
        ],
        "dimensions": dimensions,
        "measures": measures,
        "unresolved": [
            "Acceptance receipts are compact evidence summaries, not complete Harness event journals.",
            "A cited Runtime Job reference is not reinterpreted as Harness-owned execution truth.",
            "Unqualified source modelId/researchOutcome strings are omitted from the Episode.",
        ],
        "nonClaims": [
            "Episode is not Harness Agent-Run truth.",
            "Acceptance status is not a cross-domain success verdict.",
            "Historical RSI evidence does not establish open-ended recursive self-improvement.",
        ],
    }
    result["projectionDigest"] = canonical_digest(result)
    validate_episode(result)
    return result


def backfill_harness_rsi(
    records: list[tuple[str, dict[str, Any]]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    episodes = [
        project_harness_rsi_record(record, source_name=source_name)
        for source_name, record in records
    ]
    episode_ids = [row["episodeId"] for row in episodes]
    runtime_jobs = sorted(
        {
            ref["objectId"]
            for row in episodes
            for ref in row["ownerRefs"]
            if ref["ownerId"] == "runtime" and ref["objectKind"] == "job"
        }
    )
    statuses: Counter[str] = Counter()
    for row in episodes:
        for dimension in row["dimensions"]:
            if dimension["name"] == "harness.acceptance_status":
                statuses[str(dimension["value"])] += 1

    collisions = len(episode_ids) - len(set(episode_ids))
    summary: dict[str, Any] = {
        "schemaVersion": 1,
        "kind": "ordivon.experimental-episode-harness-rsi-backfill-summary",
        "sourceReceipts": len(records),
        "projectedEpisodes": len(episodes),
        "episodeIdentityCollisions": collisions,
        "citedRuntimeJobCount": len(runtime_jobs),
        "measureCount": sum(len(row["measures"]) for row in episodes),
        "statusDistribution": dict(sorted(statuses.items())),
        "episodeIdSetDigest": canonical_digest(sorted(episode_ids)),
        "projectionDigestSetDigest": canonical_digest(
            sorted(row["projectionDigest"] for row in episodes)
        ),
        "citedRuntimeJobSetDigest": canonical_digest(runtime_jobs),
        "standing": (
            "PASS_HARNESS_RSI_EPISODE_PROJECTION"
            if episodes and collisions == 0
            else "FAIL_HARNESS_RSI_EPISODE_PROJECTION"
        ),
        "claimBoundary": (
            "This proves a second owner pressure-test of the Episode core. "
            "It does not prove every cited Runtime Job is still retained by the current Runtime."
        ),
    }
    summary["summaryDigest"] = canonical_digest(summary)
    return episodes, summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", type=Path)
    parser.add_argument("episodes", type=Path)
    parser.add_argument("summary", type=Path)
    args = parser.parse_args()

    records: list[tuple[str, dict[str, Any]]] = []
    for path in sorted(args.inputs.glob("harness-rsi-p*.json")):
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise SystemExit(f"{path}: root must be an object")
        records.append((path.name, value))

    episodes, summary = backfill_harness_rsi(records)
    args.episodes.write_text(
        "".join(
            json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n"
            for row in episodes
        ),
        encoding="utf-8",
    )
    args.summary.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    if summary["standing"] != "PASS_HARNESS_RSI_EPISODE_PROJECTION":
        raise SystemExit(summary["standing"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

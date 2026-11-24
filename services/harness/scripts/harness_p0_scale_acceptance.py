#!/usr/bin/env python3
"""Produce the HHO-P0 1,000-Run / 100,000-Event scale receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import os
import subprocess
import uuid
from contextlib import contextmanager
from collections.abc import Iterator
import time
from typing import Any

from ordivon_harness.core_contracts import HarnessBoundReference, HarnessRunContract
import psycopg
from psycopg import sql

from ordivon_harness.postgres_store import PostgresHarnessStore
from ordivon_harness.store import HarnessEventAdmission, HarnessEventWrite

DIGEST_A = "sha256:" + "a" * 64
DIGEST_B = "sha256:" + "b" * 64
DIGEST_C = "sha256:" + "c" * 64
DIGEST_D = "sha256:" + "d" * 64


def _contract(index: int, created_at_ms: int) -> HarnessRunContract:
    suffix = f"{index:04d}"
    return HarnessRunContract(
        harness_run_id=f"harness-run:p0-scale:{suffix}",
        harness_implementation_id="ordivon-harness@p0-scale",
        caller_id="caller:p0-scale",
        caller_run_ref=f"trial:p0-scale:{suffix}",
        objective_ref=HarnessBoundReference(
            f"objective:p0-scale:{suffix}", "objective", DIGEST_A
        ),
        context_refs=(
            HarnessBoundReference(
                f"context:p0-scale:{suffix}", "context", DIGEST_B
            ),
        ),
        provider_id="provider:scale-fixture",
        adapter_id="adapter:scale-fixture-v1",
        requested_model_id="model:scale-fixture",
        tool_catalog_digest=DIGEST_C,
        tool_grant_digest=DIGEST_D,
        budget={"maxModelCalls": 1, "maxToolCalls": 0},
        completion_contract={"mode": "scale-fixture"},
        system_manifest_ref=HarnessBoundReference(
            f"system-manifest:p0-scale:{suffix}", "system-manifest", DIGEST_A
        ),
        created_at_ms=created_at_ms,
    )


def _canonical_digest(value: dict[str, Any]) -> str:
    payload = dict(value)
    payload.pop("integrity", None)
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, math.ceil(len(ordered) * percentile) - 1))
    return ordered[index]


def _revision() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=Path(__file__).resolve().parents[1],
        text=True, encoding="utf-8"
    ).strip()


@contextmanager
def _isolated_scale_schema(dsn: str) -> Iterator[str]:
    """Create and drop only a fresh owned schema in an explicit test database."""
    if not dsn or not dsn.strip():
        raise ValueError("HARNESS_PG_TEST_DSN is required for PostgreSQL scale acceptance")
    schema = "hpg_scale_" + uuid.uuid4().hex
    with psycopg.connect(dsn, autocommit=True) as connection:
        # No IF NOT EXISTS: a pre-existing schema is not ours to remove.
        connection.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
    try:
        yield schema
    finally:
        with psycopg.connect(dsn, autocommit=True) as connection:
            connection.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


def _source_clean() -> bool:
    return not subprocess.check_output(
        ["git", "status", "--porcelain", "--", "src", "scripts", "pyproject.toml", "uv.lock"],
        cwd=Path(__file__).resolve().parents[1], text=True,
    ).strip()


def _counts(store: PostgresHarnessStore) -> dict[str, int]:
    """Independent SQL cardinalities of the original PG owner tables."""
    result = store.connection.execute(
        """
        SELECT (SELECT count(*) FROM runs) AS runs,
               (SELECT count(*) FROM run_events) AS events,
               (SELECT count(*) FROM objects) AS objects,
               (SELECT count(*) FROM run_object_refs WHERE role='payload') AS payload_edges,
               (SELECT count(*) FROM run_object_refs) AS object_edges,
               (SELECT count(*) FROM objects o WHERE NOT EXISTS
                   (SELECT 1 FROM run_object_refs r WHERE r.digest=o.digest)) AS orphan_objects,
               (SELECT count(*) FROM run_leases) AS leases
        """
    ).fetchone()
    return {key: int(value) for key, value in result.items()}


def run_acceptance(
    *,
    dsn: str,
    run_count: int,
    events_per_run: int,
    batch_size: int,
    inspect_samples: int,
    max_write_ms: int,
    max_reopen_ms: int,
    max_inspect_p95_ms: int,
) -> dict[str, Any]:
    if run_count < 1 or events_per_run < 2:
        raise ValueError("scale acceptance requires positive Runs and at least two Events per Run")
    if not 1 <= batch_size <= 256:
        raise ValueError("batch size must be between 1 and 256")
    if inspect_samples < 1:
        raise ValueError("inspect sample count must be positive")

    with _isolated_scale_schema(dsn) as schema:
        return _run_scale(
            dsn=dsn, schema=schema, run_count=run_count, events_per_run=events_per_run,
            batch_size=batch_size, inspect_samples=inspect_samples,
            max_write_ms=max_write_ms, max_reopen_ms=max_reopen_ms,
            max_inspect_p95_ms=max_inspect_p95_ms,
        )


def _run_scale(
    *, dsn: str, schema: str, run_count: int, events_per_run: int, batch_size: int,
    inspect_samples: int, max_write_ms: int, max_reopen_ms: int,
    max_inspect_p95_ms: int,
) -> dict[str, Any]:
    revision = _revision()
    source_clean = _source_clean()
    started_at_ms = time.time_ns() // 1_000_000
    write_started = time.perf_counter_ns()
    with PostgresHarnessStore(dsn, schema=schema, initialize=True) as store:
        for run_index in range(run_count):
            created_at_ms = 1_000_000 + run_index * (events_per_run + 2)
            contract = _contract(run_index, created_at_ms)
            if store.create_run(contract) is not HarnessEventAdmission.CREATED:
                raise AssertionError("fresh scale Run unexpectedly existed")
            remaining = events_per_run - 1
            next_event = 0
            while remaining:
                count = min(remaining, batch_size)
                projection = store.load_run(contract.harness_run_id)
                lease = store.acquire_run_lease(
                    contract.harness_run_id,
                    owner_id=f"scale:{run_index}:{next_event}",
                    ttl_ms=60_000,
                    now_ms=created_at_ms + 1 + next_event,
                )
                events = tuple(
                    HarnessEventWrite(
                        event_id=f"event:p0-scale:{run_index:04d}:{next_event + offset:04d}",
                        event_kind="harness.trace-recorded",
                        data={"kind": "scale-trace", "runIndex": run_index, "eventIndex": next_event + offset},
                        recorded_at_ms=created_at_ms + 1 + next_event + offset,
                    )
                    for offset in range(count)
                )
                admission = store.append_events(
                    harness_run_id=contract.harness_run_id,
                    events=events,
                    expected_revision=projection.revision,
                    lease=lease,
                    lease_checked_at_ms=created_at_ms + 1 + next_event,
                )
                if admission is not HarnessEventAdmission.CREATED:
                    raise AssertionError("fresh scale Event batch unexpectedly existed")
                next_event += count
                remaining -= count
    write_elapsed_ms = (time.perf_counter_ns() - write_started) / 1_000_000

    expected_events = run_count * events_per_run

    reopen_started = time.perf_counter_ns()
    with PostgresHarnessStore(dsn, schema=schema) as reopened:
        doctor = reopened.doctor(full=True)
        counts = _counts(reopened)
        inspect_latencies_ms: list[float] = []
        samples = min(run_count, inspect_samples)
        for sample in range(samples):
            run_index = (sample * run_count) // samples
            run_id = f"harness-run:p0-scale:{run_index:04d}"
            inspect_started = time.perf_counter_ns()
            projection = reopened.load_run(run_id)
            events = reopened.list_run_events(run_id)
            inspect_latencies_ms.append(
                (time.perf_counter_ns() - inspect_started) / 1_000_000
            )
            if projection.revision != events_per_run or len(events) != events_per_run:
                raise AssertionError("scale Run projection differs from event history")
    reopen_elapsed_ms = (time.perf_counter_ns() - reopen_started) / 1_000_000

    checks = {
        "runCountExact": counts["runs"] == run_count,
        "eventCountExact": counts["events"] == expected_events,
        "doctorHealthy": doctor.get("healthy") is True,
        "doctorCountsExact": (
            doctor.get("runs") == run_count and doctor.get("events") == expected_events
        ),
        "doctorObjectCountExact": doctor.get("objects") == counts["objects"] == expected_events + run_count,
        "eventPayloadEdgesExact": counts["payload_edges"] == expected_events,
        "objectEdgesExact": counts["object_edges"] == expected_events + run_count,
        "noOrphanObjects": counts["orphan_objects"] == 0,
        "noOutstandingLeases": counts["leases"] == 0,
        "postgresBackend": doctor.get("storageBackend") == "postgresql",
        "writeWithinBound": write_elapsed_ms <= max_write_ms,
        "reopenAndFullDoctorWithinBound": reopen_elapsed_ms <= max_reopen_ms,
        "inspectP95UnderBound": (
            _percentile(inspect_latencies_ms, 0.95) <= max_inspect_p95_ms
        ),
    }
    receipt: dict[str, Any] = {
        "schemaVersion": 1,
        "kind": "ordivon.harness-p0-scale-acceptance",
        "implementationRevision": revision,
        "sourceStanding": ("commit-bound" if source_clean and _source_clean() and _revision() == revision else "working-tree"),
        "configuration": {
            "runCount": run_count,
            "eventsPerRun": events_per_run,
            "expectedEventCount": expected_events,
            "batchSize": batch_size,
            "inspectSamples": min(run_count, inspect_samples),
            "storageBackend": "postgresql",
            "maxWriteMs": max_write_ms,
            "maxReopenMs": max_reopen_ms,
            "maxInspectP95Ms": max_inspect_p95_ms,
        },
        "measurements": {
            "writeElapsedMs": round(write_elapsed_ms, 3),
            "reopenAndFullDoctorElapsedMs": round(reopen_elapsed_ms, 3),
            "inspectP50Ms": round(_percentile(inspect_latencies_ms, 0.50), 3),
            "inspectP95Ms": round(_percentile(inspect_latencies_ms, 0.95), 3),
        },
        "counts": counts,
        "checks": checks,
        "passed": all(checks.values()),
        "startedAtMs": started_at_ms,
        "finishedAtMs": time.time_ns() // 1_000_000,
    }
    receipt["integrity"] = {
        "algorithm": "sha256",
        "canonicalization": "ordivon-evidence-json-v1",
        "payloadDigest": _canonical_digest(receipt),
    }
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--runs", type=int, default=1_000)
    parser.add_argument("--events-per-run", type=int, default=100)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--inspect-samples", type=int, default=100)
    parser.add_argument("--max-write-ms", type=int, default=180_000)
    parser.add_argument("--max-reopen-ms", type=int, default=120_000)
    parser.add_argument("--max-inspect-p95-ms", type=int, default=1_000)
    args = parser.parse_args()

    dsn = os.environ.get("HARNESS_PG_TEST_DSN", "").strip()
    if not dsn:
        parser.error("HARNESS_PG_TEST_DSN dedicated test database is required; no SQLite fallback")
    receipt = run_acceptance(
        dsn=dsn,
        run_count=args.runs,
        events_per_run=args.events_per_run,
        batch_size=args.batch_size,
        inspect_samples=args.inspect_samples,
        max_write_ms=args.max_write_ms,
        max_reopen_ms=args.max_reopen_ms,
        max_inspect_p95_ms=args.max_inspect_p95_ms,
    )
    encoded = json.dumps(receipt, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if args.output is not None:
        if receipt["sourceStanding"] != "commit-bound":
            parser.error("refusing persistent scale evidence from an uncommitted source tree")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
        args.output.chmod(0o600)
    print(encoded, end="")
    return 0 if receipt["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

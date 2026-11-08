#!/usr/bin/env python3
"""Produce a PostgreSQL-native 1,000-Run / 100,000-Event scale receipt."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import time
from typing import Any, Iterator
import uuid

import psycopg
from psycopg import sql

from ordivon_harness.core_contracts import HarnessBoundReference, HarnessRunContract
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
        ["git", "rev-parse", "HEAD"], text=True, encoding="utf-8"
    ).strip()


@contextmanager
def _fresh_scale_schema(dsn: str) -> Iterator[str]:
    """Provision and retire only a unique test schema, not a database or old state."""
    if not dsn or not dsn.strip():
        raise ValueError("HARNESS_PG_TEST_DSN is required for native scale acceptance")
    schema = "hpg_scale_" + uuid.uuid4().hex[:20]
    try:
        with PostgresHarnessStore(dsn, schema=schema, initialize=True):
            pass
        yield schema
    finally:
        # Even partially initialized schema creation must not leave test state
        # behind after an exception; the exact randomly generated name is local.
        with psycopg.connect(dsn, autocommit=True) as connection:
            connection.execute(
                sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(schema))
            )


def _counts(dsn: str, schema: str) -> tuple[int, int, int, int, int]:
    with PostgresHarnessStore(dsn, schema=schema) as store:
        connection = store.connection
        runs = int(connection.execute("SELECT count(*) AS n FROM runs").fetchone()["n"])
        events = int(connection.execute("SELECT count(*) AS n FROM run_events").fetchone()["n"])
        objects = int(connection.execute("SELECT count(*) AS n FROM objects").fetchone()["n"])
        referenced = int(connection.execute(
            "SELECT count(DISTINCT digest) AS n FROM run_object_refs"
        ).fetchone()["n"])
        bytes_used = int(connection.execute(
            "SELECT coalesce(sum(pg_total_relation_size(c.oid)),0) AS n "
            "FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
            "WHERE n.nspname=%s AND c.relkind='r'", (schema,)
        ).fetchone()["n"])
        return runs, events, objects, referenced, bytes_used


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

    with _fresh_scale_schema(dsn) as schema:
        started_at_ms = time.time_ns() // 1_000_000
        write_started = time.perf_counter_ns()
        with PostgresHarnessStore(dsn, schema=schema) as store:
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
                            data={"kind": "scale-trace"},
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

        actual_runs, actual_events, object_count, referenced_count, schema_bytes = _counts(
            dsn, schema
        )
        expected_events = run_count * events_per_run

        reopen_started = time.perf_counter_ns()
        with PostgresHarnessStore(dsn, schema=schema) as reopened:
            doctor = reopened.doctor(full=True)
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
            "runCountExact": actual_runs == run_count,
            "eventCountExact": actual_events == expected_events,
            "doctorHealthy": doctor.get("healthy") is True,
            "doctorCountsExact": (
                doctor.get("runs") == run_count and doctor.get("events") == expected_events
            ),
            "objectCountMatchesReferencedDigests": object_count == referenced_count,
            "doctorObjectCountExact": doctor.get("objects") == object_count,
            "noUnreleasedLeases": doctor.get("leases") == 0,
            "writeWithinBound": write_elapsed_ms <= max_write_ms,
            "reopenAndFullDoctorWithinBound": reopen_elapsed_ms <= max_reopen_ms,
            "inspectP95UnderBound": (
                _percentile(inspect_latencies_ms, 0.95) <= max_inspect_p95_ms
            ),
        }
        receipt: dict[str, Any] = {
            "schemaVersion": 1,
            "kind": "ordivon.harness-pg-scale-acceptance",
            "implementationRevision": _revision(),
            "configuration": {
                "runCount": run_count,
                "eventsPerRun": events_per_run,
                "expectedEventCount": expected_events,
                "batchSize": batch_size,
                "inspectSamples": min(run_count, inspect_samples),
                "storageBackend": "postgresql",
                "schemaScope": "unique-ephemeral-test-only",
                "maxWriteMs": max_write_ms,
                "maxReopenMs": max_reopen_ms,
                "maxInspectP95Ms": max_inspect_p95_ms,
            },
            "measurements": {
                "writeElapsedMs": round(write_elapsed_ms, 3),
                "reopenAndFullDoctorElapsedMs": round(reopen_elapsed_ms, 3),
                "inspectP50Ms": round(_percentile(inspect_latencies_ms, 0.50), 3),
                "inspectP95Ms": round(_percentile(inspect_latencies_ms, 0.95), 3),
                "pgSchemaBytes": schema_bytes,
                "objectReferenceDistinctDigests": referenced_count,
                "objectRows": object_count,
            },
            "counts": {
                "runs": actual_runs,
                "events": actual_events,
                "objects": object_count,
            },
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

    dsn = os.environ.get("HARNESS_PG_TEST_DSN", "")
    if not dsn.strip():
        parser.error("HARNESS_PG_TEST_DSN is required; no SQLite fallback")
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
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
        args.output.chmod(0o600)
    print(encoded, end="")
    return 0 if receipt["passed"] else 1



if __name__ == "__main__":
    raise SystemExit(main())

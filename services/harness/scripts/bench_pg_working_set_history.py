"""Opt-in reproducible real PostgreSQL 18 Working Set history latency experiment.

Requires HARNESS_PG_TEST_DSN for a disposable PG instance; never uses production DSN.
Creates and drops unique test schemas. Use only a disposable PG instance and set
ORDIVON_DISPOSABLE_PG_BENCH=yes. All events go through canonical Harness Store
append_events, not fake SQL rows. A fixed contract and event recipe is used for both
the historical path and the bounded PostgreSQL reader. No Provider is contacted.
"""

from __future__ import annotations

from contextlib import contextmanager
import json
import math
import os
import statistics
import time
import uuid
from unittest.mock import patch

import psycopg
from psycopg import sql

from ordivon_harness.ordivon.run_continuity import EventSourcedRunContinuity
from ordivon_harness.postgres_store import PostgresHarnessStore
from ordivon_harness.store import HarnessEventWrite
from ordivon_harness.working_view import (
    AgentWorkingSetTransitionProposal,
    compile_working_view,
)
from tests.test_pc15_epistemic_control import private_contract
from tests.test_pc18_historical_cognition_recall import HistoricalCognitionRecallTests


def percentile(values: list[float], fraction: float) -> float:
    return sorted(values)[max(0, math.ceil(len(values) * fraction) - 1)]


class _EventCursor:
    def __init__(self, original, tally):
        self.original = original
        self.tally = tally

    def fetchall(self):
        started = time.perf_counter()
        records = self.original.fetchall()
        self.tally["sql_event_rows"] += len(records)
        self.tally["sql_event_ms"] += 1000 * (time.perf_counter() - started)
        return records


class _ConnectionProbe:
    def __init__(self, real, tally):
        self.real = real
        self.tally = tally

    def execute(self, query, params=None):
        q = str(query)
        started = time.perf_counter()
        cursor = self.real.execute(query, params)
        if "FROM run_events e" in q:
            self.tally["sql_event_ms"] += 1000 * (time.perf_counter() - started)
            return _EventCursor(cursor, self.tally)
        return cursor


@contextmanager
def observed(store: PostgresHarnessStore):
    tally = {"sql_event_rows": 0, "decoded_objects": 0, "sql_event_ms": 0.0}
    original_connection = store.connection
    original_decoder = store._decode_object_row

    def counted(*args, **kwargs):
        tally["decoded_objects"] += 1
        return original_decoder(*args, **kwargs)

    store.connection = _ConnectionProbe(original_connection, tally)
    store._decode_object_row = counted
    try:
        yield tally
    finally:
        store.connection = original_connection
        del store._decode_object_row


def make_run(store, events: int):
    tag = uuid.uuid4().hex[:10]
    contract = private_contract(f"latency-{events}-{tag}", max_model_calls=1, max_tool_calls=0)
    store.create_run(contract)
    continuity = EventSourcedRunContinuity(store, contract)
    _, _, _, pin_a, pin_k, _ = HistoricalCognitionRecallTests.seed_history(store, continuity)
    # More than ten real committed Working Sets, interleaved with one
    # legitimate uncommitted seed, so LIMIT+1 and last-page semantics matter.
    for i in range(11):
        current = continuity.load_current_working_set()
        next_pins = (pin_a, pin_k) if i % 2 == 0 else (pin_a,)
        continuity.apply_working_set_transition(
            AgentWorkingSetTransitionProposal(
                next_attempt_id=f"working-attempt:bench-{events}-{i}",
                pins=next_pins,
                basis="Original PG bounded pagination regression.",
            ),
            source_working_set_digest=current.digest,
            source_model_view_digest=compile_working_view(current, store).digest,
        )
    existing = len(store.list_run_events(contract.harness_run_id))
    if existing >= events:
        raise AssertionError(("too few requested events", existing, events))
    remaining = events - existing
    at = store.load_run(contract.harness_run_id).updated_at_ms
    counter = 0
    while remaining:
        batch = min(remaining, 256)
        lease = store.acquire_run_lease(
            contract.harness_run_id,
            owner_id="worker:bench-history",
            ttl_ms=5_000_000,
            now_ms=1000,
        )
        payload = tuple(
            HarnessEventWrite(
                event_id=f"event:history-bench-{events}-{tag}-{counter + j}",
                event_kind="harness.trace-recorded",
                data={"trace": f"bounded-source-{(counter + j) % 9}"},
                recorded_at_ms=at + j + 1,
            )
            for j in range(batch)
        )
        store.append_events(
            harness_run_id=contract.harness_run_id,
            events=payload,
            expected_revision=lease.run_revision,
            lease=lease,
            lease_checked_at_ms=1001,
        )
        counter += batch
        remaining -= batch
        at += batch
    actual = len(store.list_run_events(contract.harness_run_id))
    assert actual == events, (events, actual)
    return contract, continuity


def benchmark_one(dsn: str, size: int, samples: int) -> dict:
    schema = "lat_" + uuid.uuid4().hex[:20]
    try:
        with PostgresHarnessStore(dsn, schema=schema, initialize=True) as store:
            contract, continuity = make_run(store, size)

            def old():
                with (
                    patch.object(store, "list_committed_working_set_events", None),
                    patch.object(store, "find_working_set_event_sequence", None),
                ):
                    return continuity.inspect_working_set_history(limit=10)

            def new():
                return continuity.inspect_working_set_history(limit=10)

            baseline = old()
            optimized = new()
            assert baseline == optimized
            assert len(optimized["selections"]) == 10
            # Exact sequence cursors, current head and every final page.
            previous = []
            cursor = None
            while True:
                with (
                    patch.object(store, "list_committed_working_set_events", None),
                    patch.object(store, "find_working_set_event_sequence", None),
                ):
                    legacy = continuity.inspect_working_set_history(limit=3, before_sequence=cursor)
                page = continuity.inspect_working_set_history(limit=3, before_sequence=cursor)
                assert page == legacy
                previous.extend(page["selections"])
                cursor = page["nextBeforeSequence"]
                if cursor is None:
                    break
            assert previous and len(previous) >= 10
            measurements = {}
            for label, operation in (("legacy", old), ("bounded", new)):
                runs = []
                rows = []
                decoded = []
                sqltimes = []
                for i in range(samples):
                    with observed(store) as totals:
                        start = time.perf_counter()
                        result = operation()
                        runs.append(1000 * (time.perf_counter() - start))
                        assert result == baseline
                        rows.append(totals["sql_event_rows"])
                        decoded.append(totals["decoded_objects"])
                        sqltimes.append(totals["sql_event_ms"])
                measurements[label] = {
                    "p50_ms": round(statistics.median(runs), 3),
                    "p95_ms": round(percentile(runs, 0.95), 3),
                    "sql_p50_ms": round(statistics.median(sqltimes), 3),
                    "sql_rows": sorted(set(rows)),
                    "decoded_objects": sorted(set(decoded)),
                    "sample_ms": [round(value, 3) for value in runs],
                    "sample_sql_ms": [round(value, 3) for value in sqltimes],
                }
            cold = []
            for label in ("legacy", "bounded"):
                with PostgresHarnessStore(dsn, schema=schema) as other:
                    start = time.perf_counter()
                    reopened = EventSourcedRunContinuity.open(other, contract.harness_run_id)
                    if label == "legacy":
                        with (
                            patch.object(other, "list_committed_working_set_events", None),
                            patch.object(other, "find_working_set_event_sequence", None),
                        ):
                            result = reopened.inspect_working_set_history(limit=10)
                    else:
                        result = reopened.inspect_working_set_history(limit=10)
                    assert result == baseline
                    cold.append(
                        {
                            "path": label,
                            "first_context_ms": round(1000 * (time.perf_counter() - start), 3),
                        }
                    )
            return {
                "size": size,
                "actual_events": size,
                "history_selected": 10,
                "sample_count": samples,
                "warm": measurements,
                "cold": cold,
                "current_sequence": optimized["currentWorkingSetEventSequence"],
                "next_cursor": optimized["nextBeforeSequence"],
            }
    finally:
        with psycopg.connect(dsn, autocommit=True) as conn:
            conn.execute(sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(schema)))


def main():
    dsn = os.environ.get("HARNESS_PG_TEST_DSN")
    if not dsn or os.environ.get("ORDIVON_DISPOSABLE_PG_BENCH") != "yes":
        raise SystemExit("Refuse benchmark without explicitly admitted disposable PostgreSQL")
    samples = int(os.environ.get("HARNESS_HISTORY_BENCH_SAMPLES", "9"))
    if not 3 <= samples <= 100:
        raise SystemExit("sample count outside [3, 100]")
    for size in (100, 1000, 10000):
        result = benchmark_one(dsn, size, samples)
        print(json.dumps(result, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Controlled PG18 race: Run changes AFTER Harness pre-call Fence qualification.

The new revision makes that previously qualified Fence stale. This script
does not dispatch anything; the opt-in Gateway/Runtime consumer then reveals
whether native PG admission independently checks issuer currentness.
"""

from __future__ import annotations

import json
import os
import secrets
import time
from contextlib import nullcontext
from pathlib import Path

from ordivon_harness.ordivon.run_continuity import EventSourcedRunContinuity
from ordivon_harness.ordivon.run_store_port import HarnessSuperseded
from ordivon_harness.protocol import HarnessToolStepStatus
from ordivon_harness.postgres_store import PostgresHarnessStore
from ordivon_harness.store import HarnessEventWrite

dsn = os.environ["ORDIVON_R22_HARNESS_PG_DSN"]
run_id = os.environ["ORDIVON_R22_EXPECT_RUN"]
request_id = os.environ["ORDIVON_R22_EXPECT_REQUEST"]
refs = json.loads(os.environ["ORDIVON_R22_EXPECT_REFS_JSON"])
assert len(refs) == 4

with PostgresHarnessStore(dsn, schema="harness_r22_source", initialize=False) as store:
    actual_now = (
        max(
            int(time.time() * 1000),
            store.load_run(run_id).updated_at_ms,
        )
        if os.getenv("ORDIVON_R25_REAL_EPOCH_ISSUER") == "1"
        else 10**12
    )
    source = EventSourcedRunContinuity.open(store, run_id, clock_ms=lambda: actual_now)
    prepared = source.load_current_tool_step()
    after_settlement = os.getenv("ORDIVON_R24_POST_RECEIPT_REVOKE") == "1"
    if after_settlement:
        # Important: history replay of a previously-accepted Owner Job is a
        # READ of the old identity, NOT a NEW permission to dispatch.
        assert prepared.receipt is not None
        assert prepared.receipt.status is HarnessToolStepStatus.OBSERVED
        assert prepared.previous_receipt is not None
        assert prepared.previous_receipt.status is HarnessToolStepStatus.UNKNOWN
        original_receipt_digest = prepared.receipt.digest
    else:
        assert prepared.receipt is None
        original_receipt_digest = None
    assert prepared.fence is not None
    assert prepared.intent.client_request_id == request_id
    assert refs[-1]["digest"] == prepared.fence.digest
    original_generation = prepared.fence.authority_generation
    preexisting_revision = store.load_run(run_id).revision
    if after_settlement:
        # A prior UNKNOWN-to-confirmed receipt adds immutable Run events:
        # authority for a new Job is no longer at the old Fence generation.
        assert preexisting_revision >= original_generation
    else:
        assert preexisting_revision == original_generation
    gate_ready = os.getenv("ORDIVON_R25_REVOKE_PENDING")
    gate_release = os.getenv("ORDIVON_R25_REVOKE_RELEASE")
    assert bool(gate_ready) == bool(gate_release)
    # Historical post-receipt tests use original deterministic clock.
    # Same-PG issuer tests use current real PG wall time for physical TTL.
    now_ms = (
        actual_now
        if os.getenv("ORDIVON_R25_REAL_EPOCH_ISSUER") == "1"
        else (1_000_000_000_100 if after_settlement else 10**12)
    )
    with store.connection.transaction() if gate_ready else nullcontext():
        lease = store.acquire_run_lease(
            run_id,
            owner_id="test:r22-supersede",
            ttl_ms=30_000,
            now_ms=now_ms,
            expected_run_revision=preexisting_revision,
        )
        stopping = os.getenv("ORDIVON_R25_SOURCE_STOP") == "1"
        store.append_events(
            harness_run_id=run_id,
            expected_revision=lease.run_revision,
            lease=lease,
            lease_checked_at_ms=now_ms,
            events=(
                HarnessEventWrite(
                    event_id="event:r22-revision-advanced-" + secrets.token_hex(9),
                    event_kind=("harness.run-stopped" if stopping else "harness.trace-recorded"),
                    data={
                        "testOnly": (
                            "Run stopped after original pre-call Fence check"
                            if stopping
                            else "Run revision advanced after original pre-call Fence check"
                        )
                    },
                    recorded_at_ms=now_ms,
                ),
            ),
        )
        store.validate_run_history(run_id)
        if gate_ready:
            Path(gate_ready).touch()
            deadline = time.monotonic() + 20
            while not Path(gate_release).exists():
                if time.monotonic() > deadline:
                    raise TimeoutError("R25 private PG issuer writer commit gate expired")
                time.sleep(0.025)
    latest = store.load_run(run_id).revision
    assert latest == preexisting_revision + 1
    if after_settlement:
        historical_step = EventSourcedRunContinuity.open(
            store, run_id, clock_ms=lambda: now_ms + 1
        ).load_current_tool_step()
        assert historical_step.receipt is not None
        assert historical_step.receipt.digest == original_receipt_digest
        assert historical_step.previous_receipt == prepared.previous_receipt
    # Isolate the Revision/Generation failure rather than unrelated wall
    # clock expiry. This is a proven stale Run even with expiry disabled.
    try:
        source.assert_dispatch_fence_current(prepared.fence, require_unexpired=False)
    except HarnessSuperseded as error:
        assert "revision" in str(error).lower()
    else:
        raise AssertionError("Harness incorrectly accepts an older Run Revision Fence")
    print(
        json.dumps(
            {
                "standing": "FENCE_SUPERSEDED_BY_DURABLE_RUN_REVISION",
                "runId": run_id,
                "preparedRevision": original_generation,
                "previousRevision": preexisting_revision,
                "currentRevision": latest,
                "fenceDigest": prepared.fence.digest,
                "historicalReceiptDigest": original_receipt_digest,
            },
            sort_keys=True,
        )
    )

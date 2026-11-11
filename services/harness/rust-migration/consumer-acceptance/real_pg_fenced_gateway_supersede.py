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

from ordivon_harness.ordivon.run_continuity import EventSourcedRunContinuity
from ordivon_harness.ordivon.run_store_port import HarnessSuperseded
from ordivon_harness.postgres_store import PostgresHarnessStore
from ordivon_harness.store import HarnessEventWrite

dsn = os.environ["ORDIVON_R22_HARNESS_PG_DSN"]
run_id = os.environ["ORDIVON_R22_EXPECT_RUN"]
request_id = os.environ["ORDIVON_R22_EXPECT_REQUEST"]
refs = json.loads(os.environ["ORDIVON_R22_EXPECT_REFS_JSON"])
assert len(refs) == 4

with PostgresHarnessStore(dsn, schema="harness_r22_source", initialize=False) as store:
    source = EventSourcedRunContinuity.open(store, run_id, clock_ms=lambda: 10**12)
    prepared = source.load_current_tool_step()
    assert prepared.receipt is None
    assert prepared.fence is not None
    assert prepared.intent.client_request_id == request_id
    assert refs[-1]["digest"] == prepared.fence.digest
    original_generation = prepared.fence.authority_generation
    assert store.load_run(run_id).revision == original_generation
    lease = store.acquire_run_lease(
        run_id,
        owner_id="test:r22-supersede",
        ttl_ms=30_000,
        now_ms=10**12,
        expected_run_revision=original_generation,
    )
    store.append_events(
        harness_run_id=run_id,
        expected_revision=lease.run_revision,
        lease=lease,
        lease_checked_at_ms=10**12,
        events=(
            HarnessEventWrite(
                event_id="event:r22-revision-advanced-" + secrets.token_hex(9),
                event_kind="harness.trace-recorded",
                data={"testOnly": "Run revision advanced after original pre-call Fence check"},
                recorded_at_ms=10**12,
            ),
        ),
    )
    store.validate_run_history(run_id)
    latest = store.load_run(run_id).revision
    assert latest == original_generation + 1
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
                "currentRevision": latest,
                "fenceDigest": prepared.fence.digest,
            },
            sort_keys=True,
        )
    )
